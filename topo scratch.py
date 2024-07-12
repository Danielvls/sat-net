# -*- coding: utf-8 -*-
# @Time    : 2024/7/2 22:55
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : topo scratch.py

from run_stk import *
import networkx as nx
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from datetime import datetime
from functools import wraps
import random
from bisect import bisect_left


# Utility function to save changes after graph modification
def save_graph_after_modification(func):
    @wraps(func)
    def wrapper(graph, idx, *args, **kwargs):
        result = func(graph, idx, *args, **kwargs)
        if graph:
            nx.write_graphml(graph, f"./graphs/graph{idx}.graphml")
        return result

    return wrapper


class TopoBuilder:
    def __init__(self):
        self.graph = nx.Graph()
        self.node_list = []

    def truncate_times(self, time_list, format_str="%d %b %Y %H:%M:%S"):
        return [datetime.strptime(time_str.split('.')[0], format_str) for time_str in time_list]

    def round_distances(self, distances):
        return [round(distance) for distance in distances]

    def save_data(self, sat_distance, time_list):
        directory = './data'
        os.makedirs(directory, exist_ok=True)

        distance_data = [[pair, dist] for pair, dist_list in sat_distance.items() for dist in dist_list]
        distance_df = pd.DataFrame(distance_data, columns=['SatellitePair', 'Distance'])
        time_series = pd.Series(time_list, name='Time Series')

        distance_df.to_csv(f'{directory}/satellite_distances.csv', index=False)
        time_series.to_csv(f'{directory}/time_series.csv', index=False)
        print("Data saved successfully.")

    @save_graph_after_modification
    def add_bandwidth_to_edges(self, graph, idx):
        if not graph:
            print(f"Warning: No graph found to update at index {idx}.")
            return
        nx.set_edge_attributes(graph, 10240, 'bandwidth')

    @save_graph_after_modification
    def add_node_betweenness_centrality(self, graph, idx):
        if not graph:
            print(f"Warning: No graph found to update at index {idx}.")
            return
        centrality = nx.betweenness_centrality(graph)
        nx.set_node_attributes(graph, centrality, 'betweenness_centrality')

    def process_satellite_distances(self):
        sat_df = pd.read_csv('./data/satellite_distances.csv')
        distance_group = sat_df.groupby('SatellitePair')
        group_size = len(next(iter(distance_group.groups.values())))

        for i in range(group_size):
            nth_distance = distance_group.nth(i)
            graph = nx.Graph([(row['SatellitePair'].split(' to ')[0], row['SatellitePair'].split(' to ')[1],
                               {'weight': row['Distance']}) for index, row in nth_distance.iterrows()])
            nx.write_graphml(graph, f"./graphs/graph{i}.graphml")

    def add_facility_connections(self):
        directory_path = './data/fac_sat_chain'
        time_df = pd.read_csv("./data/time_series.csv")
        time_list = pd.to_datetime(time_df['Time Series']).tolist()

        for filename in filter(lambda f: f.endswith(".csv"), os.listdir(directory_path)):
            filepath = os.path.join(directory_path, filename)
            node_a, node_b = filename[:-4].split(' To ')
            df = pd.read_csv(filepath)
            for index, row in df.iterrows():
                chain_time = pd.to_datetime(row['Time'])
                idx = self.find_time_index(time_list, chain_time)
                if idx is not None:
                    graph_path = f"./graphs/graph{idx}.graphml"
                    graph = nx.read_graphml(graph_path) if os.path.exists(graph_path) else nx.Graph()
                    graph.add_edge(node_a, node_b, weight=row['Distance'], bidirectional=True)
                    nx.write_graphml(graph, graph_path)

    def find_time_index(self, time_list, time_point):
        idx = bisect_left(time_list, time_point)
        if idx < len(time_list) and time_list[idx] == time_point:
            return idx
        return None

    def generate_topology(self):
        self.process_satellite_distances()
        self.add_facility_connections()


if __name__ == "__main__":
    builder = TopoBuilder()
    builder.generate_topology()
