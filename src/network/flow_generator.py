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
from src.utils import avg_duration, minimum_bandwidth, maximum_bandwidth


class FlowGenerator:
    def __init__(self, avg_flow_num):
        # Initialize flow generator with the number of flows
        self.current_file = Path(__file__).resolve()
        self.project_root = self.current_file.parents[2]
        self.time_series_directory = self.project_root / 'data' / 'time_series.csv'
        self.graph_path = self.project_root / 'graphs'

        # get configuration
        self.avg_duration = avg_duration
        self.avg_flow_num = avg_flow_num
        self.minimum_bandwidth, self.maximum_bandwidth = minimum_bandwidth, maximum_bandwidth

        # initialize lists
        self.graph_list = []
        self.flows = []
        self.satellites = []
        self.facilities = []
        self.load_graphs()

    # generate flows
    def generate_flows(self):
        # the number of flows is Poisson distributed
        num_flows = round(np.random.poisson(self.avg_flow_num))

        # generate flows for each graph
        for index in range(len(self.graph_list)):
            graph = self.graph_list[index]

            # generate node lists for each graph
            self.satellites, self.facilities = self._generate_node_lists(graph)
            # print(f"satellites: {self.satellites}, facilities: {self.facilities}")

            for _ in range(num_flows):
                # randomly select start and target nodes
                start_node = random.choice(self.satellites)
                target_node = random.choice(self.facilities)

                # bandwidth(Mbps) is randomly generated, duration is exponentially distributed
                bandwidth = round(random.uniform(self.minimum_bandwidth, self.maximum_bandwidth), 2)
                duration = round(np.random.exponential(self.avg_duration), 2)

                # flow info
                flow = {
                    "graph_index": index,
                    "primary_path": None,
                    "backup_path": None,
                    "start_node": start_node,
                    "target_node": target_node,
                    "bandwidth": bandwidth,
                    "duration": duration
                }
                self.flows.append(flow)

        return self.flows

    def load_graphs(self):
        time_df = pd.read_csv(self.time_series_directory)
        time_series = pd.to_datetime(time_df['Time Series'])

        # Load all graphs and store them in a dictionary with their corresponding times
        for index, _ in enumerate(time_series):
            graph_file = self.graph_path / f"graph{index}.json"
            if graph_file.exists():
                try:
                    with open(graph_file, 'r') as file:
                        data = json.load(file)
                        graph = nx.node_link_graph(data)
                        self.graph_list.append(graph)
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


if __name__ == '__main__':
    pass
