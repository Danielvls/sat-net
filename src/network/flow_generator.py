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
    def __init__(self, graph_list, avg_flow_num):
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
        self.graph_list = graph_list
        self.flows = []

    # generate flows
    def generate_flows(self):
        # the number of flows is Poisson distributed
        # num_flows = round(np.random.poisson(self.avg_flow_num))
        k = 3  # k 越大，方差越小
        num_flows = round(np.mean([np.random.poisson(self.avg_flow_num) for _ in range(k)]))

        # generate flows for each graph
        for index in range(len(self.graph_list)):
            graph = self.graph_list[index]

            # generate node lists for each graph
            satellites, facilities = self._generate_node_lists(graph)
            # print(f"satellites: {self.satellites}, facilities: {self.facilities}")

            for _ in range(num_flows):
                # randomly select start and target nodes
                start_node = random.choice(satellites)
                target_node = random.choice(facilities)

                # bandwidth(Mbps) is randomly generated, duration is exponentially distributed
                # mean_bandwidth = (self.minimum_bandwidth + self.maximum_bandwidth) / 2
                # sigma = (self.maximum_bandwidth - self.minimum_bandwidth) / 6
                # bandwidth = round(random.gauss(mean_bandwidth, sigma), 2)
                # bandwidth = max(min(bandwidth, self.maximum_bandwidth), self.minimum_bandwidth)
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
