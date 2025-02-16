# -*- coding: utf-8 -*-
# @Time    : 2024/7/1 11:28
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : topo_builder.py
import json
import networkx as nx
from src.utils import save_graph_after_modification, get_time_list, approx_time, get_time_list
from bisect import bisect_left
from pathlib import Path
import pandas as pd
from src.utils.logger import Logger

logger = Logger().get_logger()

class TopoBuilder:
    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[2]
        self.graph_path = self.project_root / 'graphs'
        self.data_directory = self.project_root / 'data'
        self.sat_distance_file = self.project_root / 'data' / 'aer_data' / 'inter_satellite_distances.csv'
        self.graph_list = []
        self.time_series = get_time_list()

    def gen_topo(self):
        '''create graph for each time step'''
        for index in range(len(self.time_series)):
            graph = nx.Graph()
            self._add_sat_to_topo(graph, index)
            # self._add_fac_to_topo(graph, index)
            # self._add_bandwidth_to_edges(graph, index)



        # form graph_list
        # self.load_graphs()

        # for index in range(len(self.graph_list)):
        #     graph = self.graph_list[index]
        #     self._add_weight_to_edges(graph, index)
        #     self._add_sat_lla_to_topo(graph, index)

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
    def _add_sat_to_topo(self, graph, index):
        '''add satellite links to topo'''
        logger.info(f"Adding satellite links to topo at index {index} ...")
        try:
            sat_df = pd.read_csv(self.sat_distance_file)
            sat_df['Distance'] = sat_df['Distance'].round(0)
        except Exception as e:
            logger.error(f"Error reading satellite distance file: {e}")
            return

        try:
            # Iterate over each time step
            for index in range(len(self.time_series)):
                counter = 0
                graph = nx.Graph()
                time = self.time_series[index]
                links = sat_df[pd.to_datetime(sat_df['Time']) == time]
                
                for _, row in links.iterrows():
                    source_node = row['SourceSatellite']
                    target_node = row['TargetSatellite'] 
                    distance = row['Distance']
                    graph.add_edge(source_node, target_node, weight=distance)
                    counter += 1

                # Save graph to file
                graph_path = self.graph_path / f"graph{index}.json"
                data = nx.node_link_data(graph)
                with open(graph_path, 'w') as f:
                    json.dump(data, f, indent=4)
                logger.debug(f"Graph {index} has {counter} edges")
                
        except Exception as e:
            logger.error(f"Error adding satellite links to topo: {e}")


    # add facility to topo
    @save_graph_after_modification
    def _add_fac_to_topo(self, graph, index):
        logger.info(f"Adding facility to topo at index {index} ...")
        # Iterate over each file in the directory
        fac_sat_chains_directory = self.project_root / 'data' / 'fac_sat_chains'
        for file_path in fac_sat_chains_directory.glob('*.csv'):
            # Parse node names from the filename
            node_a, node_b = file_path.stem.split(' To ')

            # Read the file content
            df = pd.read_csv(file_path)

            # Get the current time from time_series
            current_time = pd.to_datetime(self.time_series[index])
            
            # Find the row in df that matches the current time
            matching_row = df[pd.to_datetime(df['Time']) == current_time]
            
            if not matching_row.empty:
                # Get the distance for the matching time
                distance = matching_row['Distance'].iloc[0]
                distance = distance.round(0)
                
                # Add nodes and edge with the distance
                if not graph.has_node(node_a):
                    graph.add_node(node_a)
                if not graph.has_node(node_b):
                    graph.add_node(node_b)
                    
                graph.add_edge(node_a, node_b, weight=distance)
                logger.debug(f"Edge ({node_a}, {node_b}) added to graph")

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
