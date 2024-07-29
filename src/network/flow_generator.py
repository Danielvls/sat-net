# -*- coding: utf-8 -*-
# @Time    : 2024/7/14 15:32
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : flow_generator.py

import random
import networkx as nx
# from sim_config import *
import os
import numpy as np
from pathlib import Path
import json
import pandas as pd
from scipy.stats import poisson
from datetime import timedelta


class FlowGenerator:
    def __init__(self, num_flows):
        self.current_file = Path(__file__).resolve()
        self.project_root = self.current_file.parents[2]
        self.SPEED_OF_LIGHT = 300000
        self.time_series_directory = self.project_root / 'data' / 'time_series.csv'
        self.graph_path = self.project_root / 'graphs'
        self.graph_dict = {}
        self.flows = []
        self.num_flows = num_flows
        self.satellites = []
        self.facilities = []

    def generate_flows(self):
        # Process flow updates across time-series graphs
        # start_time = pd.to_datetime(graph_dict[0]['time'])
        # print(f"start at {start_time}!")
        # indices = find_time_indices(start_time, flow['delay'], time_series)

        # generate flows for each graph
        for index in range(len(self.graph_dict)):
            graph_info = self.graph_dict.get(index)
            # print(f"this is index:{index}!")
            if graph_info:
                graph = graph_info['graph']
                # each graph generate certain amount of flows
                for _ in range(self.num_flows):
                    # sort the node list into sat and fac
                    self.satellites, self.facilities = self._generate_node_lists(graph)

                    # generate flows
                    start_node = random.choice(self.satellites)
                    target_node = random.choice(self.facilities)
                    # while target_node == start_node:
                    #     target_node = random.choice(nodes_list)
                    # package_size = round(random.uniform(2048, 4096), 2)
                    # delay = calculate_transmission_delay(graph, primary_path)
                    delay = round(random.uniform(1000, 5000), 2)

                    flow = {
                        "graph_index": index,
                        "primary_path": None,
                        "backup_path": None,
                        "start_node": start_node,
                        "target_node": target_node,
                        # "package_size": package_size,
                        "delay": delay
                    }
                    self.flows.append(flow)
        return self.flows

    def load_graphs(self):
        time_df = pd.read_csv(self.time_series_directory)
        time_series = pd.to_datetime(time_df['Time Series'])

        # Load all graphs and store them in a dictionary with their corresponding times
        for index, time_point in enumerate(time_series):
            graph_file = self.graph_path / f"graph{index}.json"
            if graph_file.exists():
                try:
                    with open(graph_file, 'r') as file:
                        data = json.load(file)
                        graph = nx.node_link_graph(data)
                        self.graph_dict[index] = {'graph': graph, 'time': time_point}
                except json.JSONDecodeError as e:
                    print(f"Error loading {graph_file}: {e}")
            else:
                print(f"File {graph_file} does not exist.")

    @staticmethod
    def _generate_node_lists(graph):
        satellites = []
        facilities = []

        # Separate satellites and ground stations
        for node in graph.nodes():
            if 'Sat' in node:
                satellites.append(node)
            elif 'Fac' in node:
                facilities.append(node)

        return satellites, facilities

    def get_flow_info(self):
        return self.flows

    def get_graph_info(self):
        return self.graph_dict


if __name__ == '__main__':
    pass
