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
import pandas as pd
from itertools import islice
from datetime import timedelta
from src.network.flow_generator import FlowGenerator
from src.utils.counter import Counter
# from path_weight_calculator import PathWeightCalculator


class FlowController:
    def __init__(self):
        flow_generator = FlowGenerator()
        self.counter = Counter()
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
        self.ground_stations = flow_generator.ground_stations

    def control_fow(self):
        for i in range(len(self.flows)):
            flow = self.flows[i]
            self.update_graph_according_to_flow(i, flow)

    def update_graph_according_to_flow(self, idx, flow):
        """set the graph according to the flow's start time and delay time"""
        start_time = pd.to_datetime(self.graph_dict[flow["graph_index"]]['time'])
        indices = self.find_time_indices(start_time, flow['delay'])

        # Distribute the service across all graphs it spans.
        for index in indices:
            graph_info = self.graph_dict.get(index)
            if graph_info:
                graph = graph_info['graph']

                if not (flow.get('primary_path') and flow.get('backup_path')):
                    primary_path_tuple, backup_path_tuple = self.find_paths_with_ksp(
                        graph, flow['start_node'], flow['target_node']
                    )
                    if primary_path_tuple and backup_path_tuple is not None:
                        self.allocate_bandwidth(graph, primary_path_tuple, backup_path_tuple)
                        flow['primary_path'] = primary_path_tuple[0]
                        flow['backup_path'] = backup_path_tuple[0]
                    else:
                        self.counter.blocked_services += 1
                        print(f"No available path found for flow {idx}")
                        break
            else:
                print(f"No graph info available for index {index}")

    @staticmethod
    def allocate_bandwidth(graph, primary_path_tuple, backup_path_tuple):
        primary_path = primary_path_tuple[0]
        backup_path = backup_path_tuple[0]
        wavelength_idx = primary_path_tuple[1]
        backup_wavelength_idx = backup_path_tuple[1]

        # calculate sharing degree

        if wavelength_idx is not None:
            # Mark wavelength as used on the primary path
            for i in range(len(primary_path) - 1):
                graph[primary_path[i]][primary_path[i + 1]]['wavelengths'][wavelength_idx] = True
                graph[primary_path[i]][primary_path[i + 1]]['bandwidth_usage'] += 1
            print(f"Allocated wavelength {wavelength_idx} on primary path {primary_path}", end=' ')
        else:
            print(f"No available wavelength on primary path {primary_path}")

        # Try to allocate wavelength on the backup path if needed

        if backup_wavelength_idx is not None:
            # Mark wavelength as used on the backup path
            for i in range(len(backup_path) - 1):
                graph[backup_path[i]][backup_path[i + 1]]['wavelengths'][backup_wavelength_idx] = True
                graph[backup_path[i]][backup_path[i + 1]]['bandwidth_usage'] += 1
            print(f"Allocated wavelength {backup_wavelength_idx} on backup path {backup_path}")
        else:
            print(f"No available wavelength on backup path {backup_path}")

    def find_paths_with_ksp(self, graph, source, target, k=4):
        # find k shortest paths from source to target
        print(f"Finding k shortest paths from {source} to {target}...", end='')
        paths = self.k_shortest_paths(graph, source, target, k)
        path_weights = []
        for path in paths:
            available_wavelength = self.find_available_wavelength(graph, path)
            if available_wavelength is not None:
                weight = self.calculate_path_weight(graph, path)
                path_weights.append((path, available_wavelength, weight))

        # sort paths by weight in descending order and return the first two paths
        path_weights.sort(key=lambda x: x[2], reverse=True)
        # return the first two paths without the weight
        if path_weights.__len__() < 2:
            return None, None
        else:
            return [(pw[0], pw[1]) for pw in path_weights[:2]]

    # def find_paths_with_ksp(self, graph, source, target, k=4):
    #     print(f"Finding k shortest paths from {source} to {target}...", end='')
    #     paths = self.k_shortest_paths(graph, source, target, k)
    #     primary_path = paths[0]
    #     primary_wavelength = self.find_available_wavelength(graph, primary_path)
    #     if primary_wavelength is None:
    #         return None, None
    #
    #     # Find backup path with shared links preference
    #     backup_path = None
    #     backup_wavelength = None
    #     for path in paths[1:]:
    #         if self.can_share_path(graph, primary_path, path):
    #             backup_wavelength = self.find_available_wavelength(graph, path)
    #             if backup_wavelength is not None:
    #                 backup_path = path
    #                 break
    #
    #     # If no shared path is found, use first fit
    #     if backup_path is None:
    #         for path in paths[1:]:
    #             backup_wavelength = self.find_available_wavelength(graph, path)
    #             if backup_wavelength is not None:
    #                 backup_path = path
    #                 break
    #
    #     if backup_path is None:
    #         return None, None
    #
    #     return (primary_path, primary_wavelength), (backup_path, backup_wavelength)

    # find time indices in the time series that are within the delay time of the flow
    def find_time_indices(self, start_time, delay):
        end_time = start_time + timedelta(seconds=delay)
        indices = []
        for i, time in enumerate(self.time_series):
            if start_time <= time <= end_time:
                indices.append(i)
        return indices

    @staticmethod
    def find_available_wavelength(graph, path):
        if len(path) < 2:
            return None
        wavelength_usage = [graph[path[i]][path[i + 1]]['wavelengths'] for i in range(len(path) - 1)]
        for wavelength_idx in range(len(wavelength_usage[0])):
            if all(not wavelength[wavelength_idx] for wavelength in wavelength_usage):
                return wavelength_idx
        return None

    def calculate_path_weight(self, graph, path, alpha=0, beta=1):
        R_total = 0
        for i in range(len(path) - 1):
            D_e = 1
            L_e = self.calculate_path_load(graph, path)
            R_e = alpha * D_e + beta / max(L_e, 1)
            R_total += R_e
        return R_total

    @staticmethod
    def k_shortest_paths(graph, source, target, k, weight=None):
        return list(
            islice(nx.shortest_simple_paths(graph, source, target, weight=weight), k)
        )

    @staticmethod
    def calculate_path_load(graph, path):
        load = 0
        for i in range(len(path) - 1):
            load += graph[path[i]][path[i + 1]]['bandwidth_usage']
        return load


