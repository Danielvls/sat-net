# -*- coding: utf-8 -*-
# @Time    : 2024/7/1 11:28
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : topo_builder.py
import json
import os
import networkx as nx
from src.utils import save_graph_after_modification, slot_num
from bisect import bisect_left
from pathlib import Path
from src.network.edge_weight_calculator import EdgeWeightCalculator
import pandas as pd


class TopoBuilder:
    def __init__(self):
        self.current_file = Path(__file__).resolve()
        self.project_root = self.current_file.parents[2]
        self.graph_path = self.project_root / 'graphs'
        self.data_directory = self.project_root / 'data'
        self.sat_distance_file = self.project_root / 'data' / 'aer_data' / 'inter_satellite_distances.csv'
        self.time_series_directory = self.project_root / 'data' / 'time_series.csv'
        self.fac_sat_chains_directory = self.project_root / 'data' / 'fac_sat_chains'

        self.slot_num = slot_num
        self.graph_list = []

        time_df = pd.read_csv(self.time_series_directory)
        self.time_series = pd.to_datetime(time_df['Time Series']).tolist()

    def gen_topo(self):
        # create graph for each time step
        for index in range(len(self.time_series)):
            graph = nx.Graph()
            self._add_sat_to_topo(graph, index)
            self._add_fac_to_topo(graph, index)
            # self._add_bandwidth_to_edges(graph, index)

        # form graph_list
        self.load_graphs()

        for index in range(len(self.graph_list)):
            graph = self.graph_list[index]
            self._add_weight_to_edges(graph, index)
            self._add_sat_lla_to_topo(graph, index)

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
                graph[u][v]['wavelengths'] = [False] * self.slot_num
                graph[u][v]['share_degree'] = [0] * self.slot_num

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

    @save_graph_after_modification
    def _add_sat_lla_to_topo(self, graph, index):
        # Load LLA data for all satellites from CSV files
        sat_lla_data = {}
        lla_reports_dir = f"{self.data_directory}/sat_lla_reports"
        if not os.path.exists(lla_reports_dir):
            print(f"Warning: LLA reports directory {lla_reports_dir} does not exist.")
            return

        # List all CSV files in the LLA reports directory
        lla_files = [f for f in os.listdir(lla_reports_dir) if f.endswith('_lla.csv')]
        if not lla_files:
            print(f"Warning: No LLA CSV files found in {lla_reports_dir}")
            return

        # Load all satellites' LLA data into a dictionary
        for filename in lla_files:
            # Extract satellite name from filename
            sat_name = filename[:-8]  # Remove '_lla.csv' from the end
            lla_filepath = os.path.join(lla_reports_dir, filename)
            lla_df = pd.read_csv(lla_filepath)
            # Ensure 'Time' column is in datetime format
            lla_df['Time'] = pd.to_datetime(lla_df['Time'])
            # Store the DataFrame in the dictionary
            sat_lla_data[sat_name] = lla_df

        # For each satellite, get the LLA data
        for sat_name, lla_df in sat_lla_data.items():
            # Iterate over each row in the DataFrame to match times with graphs
            for _, row in lla_df.iterrows():
                lla_time = row['Time']
                latitude = row['Latitude']
                longitude = row['Longitude']

                # Use find_time_index to determine the closest time index
                idx = self.find_time_index(lla_time)

                # Ensure that the found index is valid
                if idx is None or idx < 0 or idx >= len(self.graph_list):
                    print(f"Warning: Time {lla_time} not found in time series.")
                    continue
                if idx == index:
                    # Add or update the node with latitude and longitude attributes
                    if graph.has_node(sat_name):
                        # Update the node attributes
                        graph.nodes[sat_name]['latitude'] = latitude
                        graph.nodes[sat_name]['longitude'] = longitude
                    else:
                        # Add the node with latitude and longitude attributes
                        graph.add_node(sat_name, latitude=latitude, longitude=longitude)

    # add facility to topo
    @save_graph_after_modification
    def _add_fac_to_topo(self, graph, index):
        # Iterate over each file in the directory
        for filename in os.listdir(self.fac_sat_chains_directory):
            if filename.endswith(".csv"):  # Ensure we are processing CSV files
                filepath = os.path.join(self.fac_sat_chains_directory, filename)
                # Parse node names from the filename
                node_a, node_b = filename[:-4].split(' To ')

                # Read the file content
                df = pd.read_csv(filepath)

                # Iterate over each row in the DataFrame to match times with graphs
                for _, row in df.iterrows():
                    chain_time = pd.to_datetime(row['Time'])
                    distance = row['Distance']

                    # Use find_time_index to determine the correct graph index
                    idx = self.find_time_index(chain_time)

                    # Ensure that the found index matches the current index being processed
                    if idx is not None and idx == index:
                        if not graph.has_node(node_a):
                            graph.add_node(node_a)
                        if not graph.has_node(node_b):
                            graph.add_node(node_b)
                        graph.add_edge(node_a, node_b, weight=distance, bidirectional=True)
                        break

    @save_graph_after_modification
    def _add_weight_to_edges(self, graph, idx):
        def _generate_node_lists(g):
            sats = []
            facs = []
            # Separate satellites and ground stations
            for node in g.nodes():
                if 'Sat' in node:

                    sats.append(node)
                elif 'Fac' in node:
                    facs.append(node)
            return sats, facs

        if graph:
            satellites, facilities = _generate_node_lists(graph)
            # print(f"satellites: {satellites}, facilities: {facilities}")

            # compute static centrality
            bc_values_static = nx.edge_betweenness_centrality_subset(
                graph, satellites, facilities, normalized=False, weight=None)

            # Stores the intermediate centrality value as an attribute of the edge
            for edge, bc_value in bc_values_static.items():
                u, v = edge  # unpack the edge tuple
                if graph.has_edge(u, v):
                    graph[u][v]['betweenness'] = bc_value
                    # print(f"At index {idx}, Edge ({u}, {v}): Betweenness Centrality = {bc_value}")

    def find_time_index(self, target_time):
        # Use bisect_left to find the insertion position that would keep self.time_series sorted
        pos = bisect_left(self.time_series, target_time)

        # If pos is 0, it means target_time is less than all elements in self.time_series
        if pos == 0:
            return 0
        # If pos is len(self.time_series), it means target_time is greater than all elements in self.time_series
        elif pos == len(self.time_series):
            return len(self.time_series) - 1
        # Otherwise, find the closest time by comparing with the previous element
        else:
            prev_time = self.time_series[pos - 1]
            next_time = self.time_series[pos]
            # Return the index of the time which is closest to target_time
            if (target_time - prev_time) <= (next_time - target_time):
                return pos - 1
            else:
                return pos

    # @save_graph_after_modification
    # def add_weight_to_edges(self):
    #     def _generate_node_lists():
    #         # Separate satellites and ground stations
    #         for node in graph.nodes():
    #             if 'Sat' in node:
    #                 satellites.append(node)
    #             elif 'Fac' in node:
    #                 facilities.append(node)
    #
    #         return satellites, facilities
    #     for index, graph in enumerate(self.graph_list):
    #         if graph:
    #             satellites = []
    #             facilities = []
    #             satellites, facilities = _generate_node_lists()
    #             # edge_weight_calculator = EdgeWeightCalculator(
    #             #     self.graph_list,
    #             #     self.time_series,
    #             # )
    #             # print(f"satellites: {satellites}, facilities: {facilities}")
    #
    #             # compute static centrality
    #             bc_values_static = nx.edge_betweenness_centrality_subset(
    #                 graph, satellites, facilities, normalized=False, weight=None)
    #
    #             # print(f"{bc_values_static}")
    #             # Stores the intermediate centrality value as an attribute of the node
    #             for edge, bc_value in bc_values_static.items():
    #                 u, v = edge  # unpack the edge tuple
    #                 if graph.has_edge(u, v):
    #                     graph[u][v]['betweenness'] = bc_value
    #                     print(f"At index {index}, Edge ({u}, {v}): Betweenness Centrality = {bc_value}")

    def load_graphs(self):
        # Load all graphs and store them in a dictionary with their corresponding times
        for index, _ in enumerate(self.time_series):
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


if __name__ == "__main__":
    builder = TopoBuilder()
    builder.gen_topo()
