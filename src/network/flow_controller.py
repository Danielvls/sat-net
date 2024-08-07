# -*- coding: utf-8 -*-
# @Time    : 2024/7/14 16:50
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : flow_controller.py
from pathlib import Path
import pandas as pd
import math
import random
import networkx as nx
# from sim_config import *
import os
import numpy as np
from pathlib import Path
from src.utils import find_time_indices
import json
from itertools import islice
from datetime import timedelta
from src.network.flow_generator import FlowGenerator
from src.network.edge_weight_calculator import EdgeWeightCalculator
from src.utils import slot_num, slot_size
from joblib import Parallel, delayed


class NoAvailablePathException(Exception):
    pass


class FlowController:
    def __init__(self, thershold, counter, avg_flow_num):
        self.thershold = thershold
        self.counter = counter

        # Initialize flow generator with the number of flows
        flow_generator = FlowGenerator(avg_flow_num)
        self.flows = flow_generator.generate_flows()
        self.graph_list = flow_generator.graph_list
        self.satellites = flow_generator.satellites
        self.facilities = flow_generator.facilities
        self.slot_num = slot_num
        self.slot_size = slot_size

        # Get the current file path and project root directory
        self.current_file = Path(__file__).resolve()
        self.project_root = self.current_file.parents[2]

        # Define the path to the time series CSV file
        self.time_series_directory = self.project_root / 'data' / 'time_series.csv'

        # Read the time series data from the CSV file
        time_df = pd.read_csv(self.time_series_directory)

        # Convert the 'Time Series' column to datetime
        self.time_series = pd.to_datetime(time_df['Time Series'])

    def control_fow(self):
        self.counter.total_flows = len(self.flows)
        for i in range(len(self.flows)):
            flow = self.flows[i]
            self.update_graph_according_to_flow(i, flow)
            print(f"Flow {i} completed.")

    def update_graph_according_to_flow(self, idx, flow):
        # Process flow updates across time-series graphs
        start_time = pd.to_datetime(self.time_series[flow["graph_index"]])
        indices = find_time_indices(self.time_series, start_time, flow['duration'])
        print(f"flow{idx} from {flow['start_node']} to {flow['target_node']}", end="")

        # make sure there is enough resource to allocate
        primary_paths_across_graphs, backup_paths_across_graphs = self.find_resource_for_shared_backup(flow, indices)

        if primary_paths_across_graphs and backup_paths_across_graphs:
            for primary_path_info, backup_pathinfo in zip(primary_paths_across_graphs, backup_paths_across_graphs):
                index, primary_path, pp_wavelength = primary_path_info[0], primary_path_info[1], primary_path_info[2]
                backup_path, bp_wavelength = backup_pathinfo[1], backup_pathinfo[2]
                # if the length of primary path is 2, no need for backup path
                if len(primary_path) < 3:
                    print("No need for backup path...", end="")
                    self.allocate_bandwidth(self.graph_list[index], (primary_path, pp_wavelength), path_type='primary')
                    break

                # if the length of primary path is more than 2, allocate the backup path
                elif len(primary_path) > 2:
                    self.allocate_bandwidth(self.graph_list[index], (primary_path, pp_wavelength), path_type='primary')
                    self.allocate_bandwidth(self.graph_list[index], (backup_path, bp_wavelength), path_type='backup')
                    flow['primary_path'] = primary_path
                    flow['backup_path'] = backup_path

        # if no path is found, increment the counter
        else:
            self.counter.blocked_services += 1
            print(f"No available path found for flow {idx}...", end="")

    def find_resource_for_shared_backup(self, flow, indices):
        primary_paths_across_graphs = []
        backup_paths_across_graphs = []

        # find resource for both paths across all graphs
        for index in indices:
            graph = self.graph_list[index]
            primary_path_tuple = self.find_links_and_bandwidths(graph, flow, path_type='primary')
            if primary_path_tuple is None:
                return None, None
            backup_path_tuple = self.find_links_and_bandwidths(
                graph, flow, path_type='backup', existing_path=primary_path_tuple[0]
            )
            if backup_path_tuple is not None:
                primary_paths_across_graphs.append((index,) + primary_path_tuple)
                backup_paths_across_graphs.append((index,) + backup_path_tuple)
                continue
            else:
                return None, None
        return primary_paths_across_graphs, backup_paths_across_graphs

    def find_links_and_bandwidths(self, graph, flow, path_type='primary', existing_path=None):
        source = flow['start_node']
        target = flow['target_node']
        path_tuple = None
        try:
            # if path type is backup, primary path must exist
            if path_type == 'backup' and existing_path and len(existing_path) > 2:
                graph_copy = graph.copy()
                for node in existing_path[1:-2]:
                    graph_copy.remove_node(node)
                graph_to_use = graph_copy
                source = existing_path[0]
                target = existing_path[-2]
            else:
                graph_to_use = graph
            paths = self.k_shortest_paths(graph_to_use, source, target)
            for path in paths:
                available_wavelength = self.find_available_wavelength(graph, path, flow, path_type=path_type)
                if available_wavelength is not None:
                    path_tuple = (path, available_wavelength)
                    break
        except nx.NetworkXNoPath:
            return None
        return path_tuple

    def find_available_wavelength(self, graph, path, flow, path_type='primary'):
        if len(path) < 2:
            return None
        # get the wavelength status and share degree along the path
        wavelength_usage = [graph[path[i]][path[i + 1]]['wavelengths'] for i in range(len(path) - 1)]
        share_degree = [graph[path[i]][path[i + 1]]['share_degree'] for i in range(len(path) - 1)]

        # check how many slot the path need
        slots = math.ceil(flow['bandwidth'] / self.slot_size)
        continuous_bandwidth_num = 0

        # find continuous wavelength, if there is no continuous wavelength, return None
        for wavelength_idx in range(len(wavelength_usage[0]) - slots):
            if self.is_wavelength_valid(
                    graph,
                    path,
                    flow,
                    wavelength_usage,
                    share_degree,
                    wavelength_idx,
                    path_type
            ):
                continuous_bandwidth_num += 1
                if continuous_bandwidth_num == slots:
                    # print(f" use wavelength from {wavelength_idx - slots + 1} to {wavelength_idx}")
                    return wavelength_idx - slots + 1
        return None

    def is_wavelength_valid(self, graph, path, flow, wavelength_usage, share_degree, wavelength_idx, path_type):
        # if the path is primary path, the wavelength should not be shared
        if path_type == 'primary':
            # check if the wavelength along the path is all free
            if (all(wavelength[wavelength_idx] is False for wavelength in wavelength_usage) or
                    all(shares[wavelength_idx] == 0 for shares in share_degree)):
                return True
        elif path_type == 'backup':
            # if the path is not shared with any other path, the wavelength is valid
            if all(shares[wavelength_idx] == 0 for shares in share_degree):
                return True
            else:
                # if the path need to share the wavelength, check if the wavelength can be shared
                valid_for_share = True

                # if every edge in the path can share the wavelength, return the wavelength index
                for i in range(len(path) - 1):
                    if share_degree[i][wavelength_idx] > 1 or not self.is_wavelength_valid_for_share(
                            graph,
                            [path[i], path[i + 1]],
                            flow,
                            wavelength_idx,
                            threshold=self.thershold
                    ):
                        return not valid_for_share
                return valid_for_share

    def is_wavelength_valid_for_share(self, graph, edge, flow, wavelength_idx, threshold):
        share_degree = graph[edge[0]][edge[1]]['share_degree'][wavelength_idx]
        if share_degree == 1:
            edge_weight_calculator = EdgeWeightCalculator(
                self.graph_list,
                edge,
                flow['backup_path'],
                flow,
                self.time_series,
                self.satellites,
                self.facilities
            )
            edge_weight = edge_weight_calculator.calculate_edge_weight()

            # if the edge weight is less than the threshold, the wavelength can be shared
            if edge_weight <= threshold:
                return True
            else:
                return False
        else:
            return True

    @staticmethod
    def allocate_bandwidth(graph, path_tuple, path_type='primary'):
        path, wavelength_idx = path_tuple

        if wavelength_idx is not None:
            for i in range(len(path) - 1):
                edge = graph[path[i]][path[i + 1]]

                # allocate the wavelength of the primary path
                if path_type == 'primary':
                    if edge['share_degree'][wavelength_idx] == 0:
                        edge['wavelengths'][wavelength_idx] = True
                        edge['bandwidth_usage'] += 1

                # allocate the wavelength of the backup path
                elif path_type == 'backup':
                    if edge['share_degree'][wavelength_idx] == 0:
                        edge['bandwidth_usage'] += 1
                        edge['share_degree'][wavelength_idx] += 1

                    # if the wavelength is shared, increase the share degree, and set the wavelength usage to True
                    elif edge['share_degree'][wavelength_idx] == 1:
                        edge['share_degree'][wavelength_idx] += 1
                        edge['wavelengths'][wavelength_idx] = True

            # print(f"Allocated wavelength {wavelength_idx} on {path_type} path {path}...", end='')
        else:
            # print(f"No available wavelength on {path_type} path {path}...", end='')
            pass

    # def weighted_ksp(self, graph, source, target):
    #     # find k shortest paths from source to target
    #     print(f"Finding k shortest paths from {source} to {target}...", end='')
    #     paths = self.k_shortest_paths(graph, source, target)
    #     path_weights = []
    #     for path in paths:
    #         available_wavelength = self.find_available_wavelength(graph, path)
    #         if available_wavelength is not None:
    #             path_weight_calculator = PathWeightCalculator(graph, path, self.satellites, self.facilities)
    #             weight = path_weight_calculator.calculate_path_weight(path)
    #             path_weights.append((path, available_wavelength, weight))
    #
    #     # sort paths by weight in descending order and return the first two paths
    #     path_weights.sort(key=lambda x: x[2], reverse=True)
    #     # return the first two paths without the weight
    #     if path_weights.__len__() < 2:
    #         return None, None
    #     else:
    #         return [(pw[0], pw[1]) for pw in path_weights[:2]]

    def k_shortest_paths(self, graph, source, target, k=4, weight=None):
        graph_copy = graph.copy()
        self.remove_other_facilities(graph_copy, target)
        return list(
            islice(nx.shortest_simple_paths(graph_copy, source, target, weight=weight), k)
        )

    def remove_other_facilities(self, graph, target_facility):
        # Iterate over all nodes in the graph
        nodes_to_remove = [node for node in self.facilities if node != target_facility]
        graph.remove_nodes_from(nodes_to_remove)


