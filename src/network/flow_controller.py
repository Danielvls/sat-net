# -*- coding: utf-8 -*-
# @Time    : 2024/7/14 16:50
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : flow_controller.py
from pathlib import Path
import pandas as pd
import math
import re
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

from src.utils import slot_num, slot_size, timeit_decorator
# from joblib import Parallel, delayed
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed


class FlowController:
    def __init__(self, threshold, counter, flows, graph_list):
        self.threshold = threshold
        self.counter = counter
        self.flows = flows
        self.graph_list = graph_list

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

    def control_flow(self):
        self.counter.total_flows = len(self.flows)

        # Process flows
        for i in range(len(self.flows)):
            flow = self.flows[i]
            self.process_flow(i, flow)
            # print(f"Flow {i} completed.")

    def process_flow(self, idx, flow):
        # print(f"flow{idx} from {flow['start_node']} to {flow['target_node']}...", end="")

        # find the time indices within the duration of the flow
        start_time = pd.to_datetime(self.time_series[flow["graph_index"]])
        indices = find_time_indices(self.time_series, start_time, flow['duration'])

        # make sure there is enough resource to allocate
        primary_paths_across_graphs, backup_paths_across_graphs = (
            self.find_resource_across_graphs(flow, indices)
        )

        # if no path is found, increment the counter
        if not primary_paths_across_graphs or not backup_paths_across_graphs:
            self.counter.blocked_flows += 1
            # print(f"No available resource found for flow {idx}...", end="")
            # print(f"{primary_paths_across_graphs}, {backup_paths_across_graphs}")
            return
        else:
            self.sequential_allocate_wavelengths(primary_paths_across_graphs, backup_paths_across_graphs)
            # print(f"self.graph_list[{10}]: {self.graph_list[10].edges.data()}")

    # @timeit_decorator
    def find_resource_across_graphs(self, flow, indices) -> (list, list):
        # Initialize lists to store primary and backup paths across graphs
        primary_paths_across_graphs = []
        backup_paths_across_graphs = []

        # Find resources for both paths across all graphs
        for index in indices:
            graph = self.graph_list[index]
            primary_path, pp_wavelengths = self.find_path_and_wavelengths(graph, flow, path_type='primary')

            # If primary path is not found
            if not primary_path or not pp_wavelengths:
                return [], []

            # Find backup path with existing primary path
            backup_path, bp_wavelengths = self.find_path_and_wavelengths(
                graph, flow, path_type='backup', existing_path=primary_path
            )

            # If backup path is not found
            if not backup_path or not bp_wavelengths:
                if len(primary_path) == 2:
                    primary_paths_across_graphs.append(
                        [index, primary_path, pp_wavelengths])
                    backup_paths_across_graphs.append(
                        [index, primary_path, pp_wavelengths])
                break

            # If backup path is found, append to respective lists
            if backup_path and bp_wavelengths:
                primary_paths_across_graphs.append(
                    [index, primary_path, pp_wavelengths])
                backup_paths_across_graphs.append(
                    [index, backup_path, bp_wavelengths])
                continue
            else:
                return [], []
        return primary_paths_across_graphs, backup_paths_across_graphs

    # @timeit_decorator
    def find_path_and_wavelengths(self, graph, flow, path_type='primary', existing_path=None) -> (list, list):
        # find path and wavelenghts for a single flow and graph
        def remove_other_facilities(_graph):
            pattern = r'^Facility'  # 假设设施节点名称以 'facility' 开头
            facilities_to_remove = [node for node in _graph.nodes() if
                                    re.match(pattern, node) and node != flow['target_node']]
            _graph.remove_nodes_from(facilities_to_remove)

        def k_shortest_paths(_graph, _source, _target, k=4, weight=None):
            return list(
                islice(nx.shortest_simple_paths(_graph, _source, _target, weight=weight), k)
            )
        try:
            # Create a copy of the graph
            graph_copy = graph.copy()

            # Remove other facilities from the graph
            remove_other_facilities(graph_copy)

            # If path type is backup, primary path must exist
            if path_type == 'primary':
                source = flow['start_node']
                target = flow['target_node']
            elif path_type == 'backup' and existing_path:
                if len(existing_path) > 2:
                    # Remove edges explicitly between intermediate nodes
                    for i in range(1, len(existing_path) - 1):
                        start_node = existing_path[i - 1]
                        end_node = existing_path[i]
                        if graph_copy.has_edge(start_node, end_node):
                            graph_copy.remove_edge(start_node, end_node)
                            # print(f"Removed edge: {start_node} -> {end_node}")
                    source = existing_path[0]
                    target = existing_path[-2]
                else:
                    # If only two nodes remain, no need to back up
                    source = existing_path[0]
                    target = existing_path[-1]
            else:
                return [], []

            paths = k_shortest_paths(graph_copy, source, target)
            # print(f"found {path_type} paths: {paths}")
            for path in paths:
                wavelength_list = self.find_continuous_wavelengths(graph_copy, path, flow, path_type)
                if wavelength_list:
                    # print(f"found {path_type} path: {path}, wavelength_list: {wavelength_list}")
                    return [path, wavelength_list]
            return [], []
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return [], []

    def find_continuous_wavelengths(self, graph, path, flow, path_type) -> list:

        # Check how many slots the path needs
        slots = math.ceil(flow['bandwidth'] / self.slot_size)
        continuous_bandwidth_num = 0
        wavelength_indices = list(range(self.slot_num))

        # Find continuous wavelengths;
        for i in range(len(path) - 1):
            edge = graph[path[i]][path[i + 1]]
            current_available_wavelengths = []
            if graph.has_edge(path[i], path[i + 1]):
                for wavelength_idx in wavelength_indices:
                    # check if the wavelength is available
                    if path_type == 'primary':
                        # if the wavelength is not shared, it is available for primary path
                        if not edge['wavelengths'][wavelength_idx] and not edge['share_degree'][wavelength_idx]:
                            continuous_bandwidth_num += 1
                            current_available_wavelengths.append(wavelength_idx)
                        else:
                            continuous_bandwidth_num = 0
                            current_available_wavelengths = []

                    # if the share degree is less than 2, it is available for backup path
                    elif path_type == 'backup':
                        # For backup paths, check if the share degree is less than 2
                        if edge['share_degree'][wavelength_idx] == 0:
                            continuous_bandwidth_num += 1
                            current_available_wavelengths.append(wavelength_idx)
                        elif edge['share_degree'][wavelength_idx] == 1 and self.is_valid_for_share(flow, path, i):
                            current_available_wavelengths.append(wavelength_idx)
                            continuous_bandwidth_num += 1
                        else:
                            continuous_bandwidth_num = 0
                            current_available_wavelengths = []

                    if continuous_bandwidth_num >= slots:
                        # print(f"Found continuous wavelengths on edge: {path[i]} - {path[i + 1]}")
                        return current_available_wavelengths[:slots]
            else:
                return []

            # Update the list of available wavelengths
            wavelength_indices = current_available_wavelengths

            # Check if the number of available wavelengths is less than required slots
            if len(wavelength_indices) < slots:
                # print(f"Insufficient continuous wavelengths on edge: {path[i]} - {path[i + 1]}")
                return []

        # If enough continuous wavelengths are available, return the list
        # print(f"Use wavelengths from {wavelength_indices[0]} to"
        #       f" {wavelength_indices[slots - 1]} for path: {path}")
        return wavelength_indices[:slots]

    # @timeit_decorator
    def sequential_allocate_wavelengths(self, primary_paths_across_graphs, backup_paths_across_graphs):
        # First, handle all primary paths
        primary_results = []
        for path_info in primary_paths_across_graphs:
            result = self.allocate_wavelengths(
                graph_index=path_info[0],
                graph=self.graph_list[path_info[0]],
                path=path_info[1],
                wavelengths=path_info[2],
                path_type='primary'
            )
            primary_results.append(result)

        # Update graph_list with results from primary path processing
        for result in primary_results:
            graph_index, updated_graph = result
            self.graph_list[graph_index] = updated_graph

        # Prepare tasks for backup paths only if the primary path length is 3 or more
        backup_results = []
        for path_info, backup_path_info in zip(primary_paths_across_graphs, backup_paths_across_graphs):
            if len(path_info[1]) >= 3:  # Check if a backup path is needed
                result = self.allocate_wavelengths(
                    graph_index=backup_path_info[0],
                    graph=self.graph_list[backup_path_info[0]],
                    path=backup_path_info[1],
                    wavelengths=backup_path_info[2],
                    path_type='backup'
                )
                backup_results.append(result)

        # Update graph_list with results from backup path processing
        for result in backup_results:
            graph_index, updated_graph = result
            self.graph_list[graph_index] = updated_graph

    @staticmethod
    def allocate_wavelengths(graph_index, graph, path, wavelengths, path_type='primary'):
        for i in range(len(path) - 1):
            edge = graph[path[i]][path[i + 1]]
            for wavelength_idx in wavelengths:
                if wavelength_idx is not None:
                    if path_type == 'primary':
                        if edge['share_degree'][wavelength_idx] == 0:
                            edge['wavelengths'][wavelength_idx] = True
                            edge['bandwidth_usage'] += 1
                    elif path_type == 'backup':
                        if edge['share_degree'][wavelength_idx] == 0:
                            edge['bandwidth_usage'] += 1
                            edge['share_degree'][wavelength_idx] += 1
                        elif edge['share_degree'][wavelength_idx] > 0:
                            edge['share_degree'][wavelength_idx] += 1
                            edge['bandwidth_usage'] += 1
                            edge['wavelengths'][wavelength_idx] = True

        return graph_index, graph

    def is_valid_for_share(self, flow, path, idx) -> bool:

        t = self.time_series[flow['graph_index']]
        delta_t = flow['duration']
        indices = find_time_indices(self.time_series, t, delta_t)
        total_interval_time = len(indices)
        betweenness = 0

        for index in indices:
            graph = self.graph_list[index]
            if graph.has_edge(path[idx], path[idx + 1]):
                edge = graph[path[idx]][path[idx + 1]]
                betweenness += edge['betweenness']
            else:
                return False
        betweenness /= total_interval_time

        if betweenness < self.threshold:
            return True
        else:
            return False





