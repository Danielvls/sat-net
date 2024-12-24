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
from src.utils import Counter


class FlowController:
    def __init__(self, flows, graph_list, threshold=100):
        self.threshold = threshold
        self.counter = Counter()
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

    # process flows one by one
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
        if primary_paths_across_graphs is None or backup_paths_across_graphs is None:
            self.counter.increment_blocked_flows()
            # print(f"No available resource found for flow {idx}...", end="")
            # print(f"{primary_paths_across_graphs}, {backup_paths_across_graphs}")
            return
        else:
            self.sequential_allocate_wavelengths(primary_paths_across_graphs, backup_paths_across_graphs)
            # print(f"self.graph_list[{10}]: {self.graph_list[10].edges.data()}")

    # @timeit_decorator
    def find_resource_across_graphs(self, flow, indices):
        # Initialize lists to store primary and backup paths across graphs
        primary_paths_across_graphs = []
        backup_paths_across_graphs = []

        for index in indices:
            graph = self.graph_list[index]

            primary_path, pp_wavelength = self.find_path_and_wavelength(graph, flow, path_type='primary')

            # If primary path is not found
            if primary_path is None or pp_wavelength is None:
                return None, None

            # if 0 hop between satellite, no need for backup
            elif len(primary_path) == 2:
                primary_paths_across_graphs.append(
                    [index, primary_path, pp_wavelength])
                backup_paths_across_graphs.append(None)
                # print(f"Flow {flow['start_node']} to {flow['target_node']} has a 0-hop path between satellite.")
            else:

                # Find backup path with existing primary path
                # make sure the length of primary path is greater than 2
                backup_path, bp_wavelength = self.find_path_and_wavelength(
                    graph, flow, path_type='backup', existing_path=primary_path
                )

                # If backup path is not found,stop the loop and return None
                if backup_path is None or bp_wavelength is None:
                    return None, None
                else:
                    primary_paths_across_graphs.append(
                        [index, primary_path, pp_wavelength])
                    backup_paths_across_graphs.append(
                        [index, backup_path, bp_wavelength])

        return primary_paths_across_graphs, backup_paths_across_graphs

    def find_path_and_wavelength(self, graph, flow, path_type='primary', existing_path=None):
        # remove the facilities who is not the target node
        def remove_other_facilities(_graph):
            pattern = r'^Facility'
            facilities_to_remove = [node for node in _graph.nodes() if
                                    re.match(pattern, node) and node != flow['target_node']]
            _graph.remove_nodes_from(facilities_to_remove)

        def k_shortest_paths(_graph, _source, _target, k=4, weight=None):
            return list(
                islice(nx.shortest_simple_paths(_graph, _source, _target, weight=weight), k)
            )
        try:
            # Create a copy of the graph for path calculation
            graph_copy = graph.copy()

            # Remove other facilities from the graph
            remove_other_facilities(graph_copy)

            if path_type == 'primary':
                source = flow['start_node']
                target = flow['target_node']

            # if the pp exist, find backup path
            else:
                # Remove edges explicitly between intermediate nodes
                # remove the edge from the first satellite to feedback satellite
                for i in range(1, len(existing_path) - 1):
                    start_node = existing_path[i - 1]
                    end_node = existing_path[i]
                    if graph_copy.has_edge(start_node, end_node):
                        graph_copy.remove_edge(start_node, end_node)
                        # print(f"Removed edge: {start_node} -> {end_node}")

                # Remove target facility from the graph_copy
                target_facility = flow['target_node']
                if graph_copy.has_node(target_facility):
                    graph_copy.remove_node(target_facility)

                source = existing_path[0]
                target = existing_path[-2]

            paths = k_shortest_paths(graph_copy, source, target)
            # print(f"found {path_type} paths: {paths}")
            for path in paths:
                wavelength_id = self.find_available_wavelength(graph_copy, path, path_type)
                if wavelength_id is not None:
                    # print(f"found {path_type} path: {path}, wavelength_id {wavelength_id}")
                    return [path, wavelength_id]
            return None, None
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None, None

    def find_available_wavelength(self, graph, path, path_type='primary'):
        wavelength_usage = [graph[path[i]][path[i + 1]]['wavelengths'] for i in range(len(path) - 1)]
        # print(f"found {path}")
        # print(f"wavelength usage: {wavelength_usage[0]}")
        share_degree = [graph[path[i]][path[i + 1]]['share_degree'] for i in range(len(path) - 1)]

        for wavelength_idx in range(len(wavelength_usage[0])):
            # check if the wavelength is not used
            if path_type == 'primary':

                # if the path is primary path, check if the wavelength is not shared
                if (all(wavelength[wavelength_idx] is False for wavelength in wavelength_usage) or
                        all(shares[wavelength_idx] == 0 for shares in share_degree)):
                    # print(f"wavelength {wavelength_idx} is available for primary path")
                    return wavelength_idx
            elif path_type == 'backup':
                if all(wavelength[wavelength_idx] is False for wavelength in wavelength_usage):
                    # 遍历每条链路，如果 share_degree 为 1，则调用 is_valid_for_share() 进行判断
                    valid_for_share = [
                        self.is_valid_for_share(graph, path, i) if shares[wavelength_idx] == 1 else True
                        for i, shares in enumerate(share_degree)
                    ]
                    # 最后的判断条件：每个链路满足 valid_for_share 或者共享度为 0
                    if all(valid for valid in valid_for_share):
                        return wavelength_idx
        return None

    # @timeit_decorator
    def sequential_allocate_wavelengths(self, primary_paths_across_graphs, backup_paths_across_graphs):
        # Allocate wavelengths for primary paths and update graphs
        for path_info in primary_paths_across_graphs:
            graph_index, updated_graph = self.allocate_wavelengths(
                graph_index=path_info[0],
                graph=self.graph_list[path_info[0]],
                path=path_info[1],
                wavelength_idx=path_info[2],
                path_type='primary'
            )
            self.graph_list[graph_index] = updated_graph

        # Allocate wavelengths for all backup paths and update graphs
        for backup_info in backup_paths_across_graphs:
            if backup_info is not None:
                graph_index, updated_graph = self.allocate_wavelengths(
                    graph_index=backup_info[0],
                    graph=self.graph_list[backup_info[0]],
                    path=backup_info[1],
                    wavelength_idx=backup_info[2],
                    path_type='backup'
                )
                self.graph_list[graph_index] = updated_graph
            else:
                continue

    def allocate_wavelengths(self, graph_index, graph, path, wavelength_idx, path_type='primary'):
        for i in range(len(path) - 1):
            # edge is the networkx edge between two nodes
            edge = graph[path[i]][path[i + 1]]

            # link is tuple of source and destination nodes
            link = (path[i], path[i + 1])

            if wavelength_idx is not None:
                if path_type == 'primary':
                    if edge['share_degree'][wavelength_idx] == 0:
                        edge['wavelengths'][wavelength_idx] = True
                        self.counter.increase_link_usage(link)
                elif path_type == 'backup':
                    if edge['share_degree'][wavelength_idx] == 0:
                        edge['share_degree'][wavelength_idx] += 1
                        self.counter.increase_link_usage(link)
                    elif edge['share_degree'][wavelength_idx] > 0:
                        edge['share_degree'][wavelength_idx] += 1
                        edge['wavelengths'][wavelength_idx] = True
        return graph_index, graph

    def is_valid_for_share(self, graph, path, idx) -> bool:
        if graph.has_edge(path[idx], path[idx + 1]):
            edge = graph[path[idx]][path[idx + 1]]
            betweenness = edge['betweenness']
            if betweenness < self.threshold:  # threshold 需要在外部定义或作为参数传递
                return True
            else:
                return False
        else:
            return False

    def is_valid_for_share_tv(self, flow, path, idx) -> bool:
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



