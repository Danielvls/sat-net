# -*- coding: utf-8 -*-
# @Time    : 2024/7/1 11:28
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : topo_builder.py


import os
import networkx as nx
import pandas as pd
from utils import save_graph_after_modification
from run_stk import *
from bisect import bisect_left


class TopoBuilder:
    def __init__(self):
        self.node_list = []
        self.graph_path = f"./graphs"
        self.data_directory = './data'

    @staticmethod
    def find_time_index(self, time_list, target_time):
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

    def gen_topo(self):
        time_df = pd.read_csv(f"{self.data_directory}/time_series.csv")
        time_series = time_df['Time Series']

        # create graph for each time step
        for index in range(len(time_series)):
            graph = nx.Graph()
            self._add_sat_to_topo(graph, index)
            self._add_fac_to_topo(graph, index)
            self._add_bandwidth_to_edges(graph, index)

    @save_graph_after_modification
    def _add_bandwidth_to_edges(self, graph, index):
        if graph:
            for u, v in graph.edges():
                graph[u][v]['bandwidth'] = 1024 * 10

    # add satellite links to topo
    @save_graph_after_modification
    def _add_sat_to_topo(self, graph, index):
        # generate sat links
        sat_df = pd.read_csv(f'{self.data_directory}/satellite_distances.csv')
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
    def _add_fac_to_topo(self, graph, index):
        directory_path = f"{self.data_directory}/fac_sat_chain"
        time_df = pd.read_csv(f"{self.data_directory}/time_series.csv")
        time_list = pd.to_datetime(time_df['Time Series']).tolist()

        # Iterate over each file in the directory
        for filename in os.listdir(directory_path):
            if filename.endswith(".csv"):  # Ensure we are processing CSV files
                filepath = os.path.join(directory_path, filename)
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

                        print(f"Edge from {node_a} to {node_b} with distance {distance} added to graph at index {idx}.")


if __name__ == "__main__":
    builder = TopoBuilder()
    builder.gen_topo()
