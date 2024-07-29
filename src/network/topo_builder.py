# -*- coding: utf-8 -*-
# @Time    : 2024/7/1 11:28
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : topo_builder.py

import os
import networkx as nx
from src.utils import save_graph_after_modification
from bisect import bisect_left
from pathlib import Path
import pandas as pd


class TopoBuilder:
    def __init__(self):
        self.current_file = Path(__file__).resolve()
        self.project_root = self.current_file.parents[2]
        self.node_list = []
        self.graph_path = self.project_root / 'graphs'
        self.sat_distance_file = self.project_root / 'data' / 'inter_satellite_distances.csv'
        self.time_series_directory = self.project_root / 'data' / 'time_series.csv'
        self.fac_sat_chain_directory = self.project_root / 'data' / 'fac_sat_chains'

    def gen_topo(self):
        time_df = pd.read_csv(self.time_series_directory)
        time_series = time_df['Time Series']

        # create graph for each time step
        for index in range(len(time_series)):
            graph = nx.Graph()
            self._add_sat_to_topo(graph, index)
            self._add_fac_to_topo(graph, index)
            self._add_bandwidth_to_edges(graph, index)

    @save_graph_after_modification
    def _add_bandwidth_to_edges(self, graph, index):
        if not graph:
            print("Warning: No graph provided or graph is empty.")
            return

        if not graph.edges():
            print("Warning: The graph has no edges.")
            return

        if graph:
            for u, v in graph.edges():
                # supose all wavelengths are available
                graph[u][v]['wavelengths'] = [False] * 10
                graph[u][v]['bandwidth_usage'] = 0
                graph[u][v]['share_degree'] = [0] * 10
                # graph[u][v]['wavelengths'][0] = True  # 假设第一个波长通道被占用

    # add satellite links to topo
    @save_graph_after_modification
    def _add_sat_to_topo(self, graph, index):
        # generate sat links
        sat_df = pd.read_csv(self.sat_distance_file)
        # sat_df['Distance'] = sat_df['Distance'].round(0)

        # calculate time steps
        time_steps = len(sat_df) // len(sat_df['SatellitePair'].unique())

        # Iterate over each time step
        for i in range(time_steps):
            for j in range(i, len(sat_df), time_steps):
                row = sat_df.iloc[j]
                node1, node2 = row['SatellitePair'].split(' to ')
                distance = row['Distance']

                # 添加边到图中
                graph.add_edge(node1, node2, weight=distance)

            # print(graph.edges(data=True))

            # write in file
            # nx.write_graphml(graph, f"./graphs/graph{i}.graphml")

    # add facility to topo
    @save_graph_after_modification
    def _add_fac_to_topo(self, graph, index):
        time_df = pd.read_csv(self.time_series_directory)
        time_list = pd.to_datetime(time_df['Time Series']).tolist()

        # Iterate over each file in the directory
        for filename in os.listdir(self.fac_sat_chain_directory):
            if filename.endswith(".csv"):  # Ensure we are processing CSV files
                filepath = os.path.join(self.fac_sat_chain_directory, filename)
                # Parse node names from the filename
                node_a, node_b = filename[:-4].split(' To ')

                # Read the file content
                df = pd.read_csv(filepath)

                # Iterate over each row in the DataFrame to match times with graphs
                for _, row in df.iterrows():
                    chain_time = pd.to_datetime(row['Time'])
                    distance = row['Distance']

                    # Use find_time_index to determine the correct graph index
                    idx = self.find_time_index(time_list, chain_time)

                    # Ensure that the found index matches the current index being processed
                    if idx is not None and idx == index:
                        if not graph.has_node(node_a):
                            graph.add_node(node_a)
                        if not graph.has_node(node_b):
                            graph.add_node(node_b)
                        graph.add_edge(node_a, node_b, weight=distance, bidirectional=True)
                        break

    @staticmethod
    def find_time_index(time_list, target_time):
        # Use bisect_left to find the insertion position that would keep time_list sorted
        pos = bisect_left(time_list, target_time)

        # If pos is 0, it means target_time is less than all elements in time_list
        if pos == 0:
            return 0
        # If pos is len(time_list), it means target_time is greater than all elements in time_list
        elif pos == len(time_list):
            return len(time_list) - 1
        # Otherwise, find the closest time by comparing with the previous element
        else:
            prev_time = time_list[pos - 1]
            next_time = time_list[pos]
            # Return the index of the time which is closest to target_time
            if (target_time - prev_time) <= (next_time - target_time):
                return pos - 1
            else:
                return pos


if __name__ == "__main__":
    builder = TopoBuilder()
    builder.gen_topo()
