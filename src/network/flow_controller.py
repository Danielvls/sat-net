# -*- coding: utf-8 -*-
# @Time    : 2024/7/14 16:50
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : flow_controller.py
from pathlib import Path
import pandas as pd
import random
import networkx as nx
# from sim_config import *
import os
import numpy as np
from pathlib import Path
import json
from itertools import islice
from datetime import timedelta
from src.network.flow_generator import FlowGenerator
# from path_weight_calculator import PathWeightCalculator


class FlowController:
    def __init__(self, counter):
        flow_generator = FlowGenerator()
        self.counter = counter
        flow_generator.load_graphs()
        self.flows = flow_generator.generate_flows()
        self.num_flows = flow_generator.num_flows
        self.graph_dict = flow_generator.graph_dict
        self.current_file = Path(__file__).resolve()
        self.project_root = self.current_file.parents[2]
        self.time_series_directory = self.project_root / 'data' / 'time_series.csv'
        time_df = pd.read_csv(self.time_series_directory)
        self.time_series = pd.to_datetime(time_df['Time Series'])
        self.satellites = flow_generator.satellites
        self.facilities = flow_generator.facilities

    def control_fow(self):
        for i in range(len(self.flows)):
            flow = self.flows[i]
            self.update_graph_according_to_flow(i, flow)
            print(f"Flow {i} completed.")

    def update_graph_according_to_flow(self, idx, flow):
        """set the graph according to the flow's start time and delay time"""
        start_time = pd.to_datetime(self.graph_dict[flow["graph_index"]]['time'])
        indices = self.find_time_indices(start_time, flow['delay'])

        print(f"Allocating bandwidth for flow {idx}...", end="")

        # Distribute the service across all graphs it spans.
        for index in indices:
            graph_info = self.graph_dict.get(index)
            if graph_info:
                graph = graph_info['graph']

                if not (flow.get('primary_path') and flow.get('backup_path')):
                    primary_path_tuple, backup_path_tuple = self.use_shared_backup_path(
                        graph, flow['start_node'], flow['target_node']
                    )

                    # if the
                    if primary_path_tuple and backup_path_tuple:

                        # if the length of primary path is 2, no need for backup path
                        if len(primary_path_tuple[0]) == 2:
                            print("No need for backup path...", end="")
                            self.allocate_bandwidth(graph, primary_path_tuple, path_type='primary')

                        # if the length of primary path is more than 2, allocate the backup path
                        elif len(primary_path_tuple[0]) >= 2:
                            self.allocate_bandwidth(graph, primary_path_tuple, path_type='primary')
                            self.allocate_bandwidth(graph, backup_path_tuple, path_type='backup')
                            flow['primary_path'] = primary_path_tuple[0]
                            flow['backup_path'] = backup_path_tuple[0]

                    # if no path is found, increment the counter
                    else:
                        self.counter.blocked_services += 1
                        print(f"No available path found for flow {idx}")
                        break
            else:
                print(f"No graph info available for index {index}")

    def use_shared_backup_path(self, graph, source, target):
        primary_path_tuple = self.find_primary_path(graph, source, target)
        if primary_path_tuple is None:
            return None, None
        backup_path_tuple = self.find_backup_path(graph, source, target, primary_path_tuple[0])
        return primary_path_tuple, backup_path_tuple

    def find_primary_path(self, graph, source, target):
        paths = self.k_shortest_paths(graph, source, target)
        primary_path_tuple = None
        for path in paths:
            available_wavelength = self.find_available_wavelength(graph, path, path_type='primary')
            if available_wavelength is not None:
                primary_path_tuple = (path, available_wavelength)
                break
        return primary_path_tuple

    def find_backup_path(self, graph, start_node, target_node, shortest_path):
        try:
            graph_copy = graph.copy()
            backup_path_tuple = None

            # remove the nodes between the start and target nodes
            if len(shortest_path) > 2:
                for node in shortest_path[1:-1]:
                    graph_copy.remove_node(node)

            paths = self.k_shortest_paths(graph_copy, start_node, target_node)
            for path in paths:
                available_wavelength = self.find_available_wavelength(graph, path, path_type='backup')
                if available_wavelength is not None:
                    backup_path_tuple = (path, available_wavelength)
                    break
            return backup_path_tuple

        except nx.NetworkXNoPath:
            return None

    @staticmethod
    def find_available_wavelength(graph, path, path_type='primary'):
        if len(path) < 2:
            return None
        wavelength_usage = [graph[path[i]][path[i + 1]]['wavelengths'] for i in range(len(path) - 1)]
        share_degree = [graph[path[i]][path[i + 1]]['share_degree'] for i in range(len(path) - 1)]

        for wavelength_idx in range(len(wavelength_usage[0])):
            # check if the wavelength is not used
            if path_type == 'primary':
                # if the path is primary path, check if the wavelength is not shared
                if (all(wavelength[wavelength_idx] is False for wavelength in wavelength_usage) or
                        all(shares[wavelength_idx] == 0 for shares in share_degree)):
                    return wavelength_idx
            elif path_type == 'backup':
                if all(shares[wavelength_idx] < 2 for shares in share_degree):
                    return wavelength_idx
        return None

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

                    # if the wavelength is shared, increase the share degree
                    elif edge['share_degree'][wavelength_idx] == 1:
                        edge['share_degree'][wavelength_idx] += 1
                        edge['wavelengths'][wavelength_idx] = True

            print(f"Allocated wavelength {wavelength_idx} on {path_type} path {path}...", end='')
        else:
            pass
            print(f"No available wavelength on {path_type} path {path}")

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

    # find time indices in the time series that are within the delay time of the flow
    def find_time_indices(self, start_time, delay):
        end_time = start_time + timedelta(seconds=delay)
        indices = []
        for i, time in enumerate(self.time_series):
            if start_time <= time <= end_time:
                indices.append(i)
        return indices

    def k_shortest_paths(self, graph, source, target, k=4, weight=None):
        graph_copy = graph.copy()
        self.remove_other_facilities(graph_copy, target)
        return list(
            islice(nx.shortest_simple_paths(graph_copy, source, target, weight=weight), k)
        )

    import networkx as nx

    def remove_other_facilities(self, graph, target_facility):
        # Iterate over all nodes in the graph
        nodes_to_remove = [node for node in self.facilities if node != target_facility]
        graph.remove_nodes_from(nodes_to_remove)




