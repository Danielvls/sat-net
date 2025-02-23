# -*- coding: utf-8 -*-
# @Time    : 2024/7/14 16:50
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : flow_controller.py

import pandas as pd
import math
import re
import random
import networkx as nx
import json
import numpy as np

from pathlib import Path
from itertools import islice

from src.utils import Counter, Logger

logger = Logger().get_logger()

class FlowController:
    def __init__(self, flows, graph_list):
        self.counter = Counter()
        self.flows = flows
        self.graph_list = graph_list
        BANDWIDTH = 10  # 10 Gbps
        for graph in self.graph_list:
            for edge in graph.edges():
                graph[edge[0]][edge[1]]['bandwidth'] = BANDWIDTH  # 单位：Gbps

        # Get the current file path and project root directory
        self.current_file = Path(__file__).resolve()
        self.project_root = self.current_file.parents[2]
        
    def control_flow(self):
        logger.info("Starting flow control...")
        self.counter.total_flows = len(self.flows)

        # Process flows
        for i in range(len(self.flows)):
            flow = self.flows[i]
            self.process_flow(i, flow)
            logger.debug(f"Flow {i} completed.")


    # process flows one by one
    def process_flow(self, idx, flow):
        logger.debug(f"Processing flow {idx} from {flow['start_node']} to {flow['target_node']}...")

        start_index = flow["graph_index"]
        end_index = start_index + flow["duration"]

        # ensure end_index is not greater than the length of the graph_list
        end_index = min(end_index, len(self.graph_list))

        for graph in [self.graph_list[i] for i in range(start_index, end_index)]:
            primary_path = self.find_path(graph, flow)
            
            # Only try to find backup path if primary path exists
            backup_path = None
            if primary_path is not None:
                backup_path = self.find_path(graph, flow, path_type='backup', existing_path=primary_path)

            graph_time = graph.graph.get('time', 'Unknown')
            
            # Only allocate resources if both paths are found
            if primary_path is not None and backup_path is not None:
                self.allocate_resource(graph, flow, primary_path)
                self.allocate_resource(graph, flow, backup_path)
                logger.info(f"Successfully allocated both paths for flow {idx} at time {graph_time}")
                logger.debug(f"Primary path: {primary_path}")
                logger.debug(f"Backup path: {backup_path}")
            else:
                if primary_path is None:
                    logger.warning(f"Failed to find primary path for flow {idx} at time {graph_time}")
                else:
                    logger.warning(f"Failed to find backup path for flow {idx} at time {graph_time}")


    def find_path(self, graph, flow, path_type='primary', existing_path=None):
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
            for path in paths:
                if self.check_resource(flow, path):
                    logger.debug(f"found {path_type} path: {path}")
                    return path
            return None
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None
     
    def check_resource(self, flow, path):
        """
        Check if there's enough bandwidth along the path for the flow
        
        Args:
            flow: Flow dictionary containing bandwidth requirement
            path: List of nodes representing the path
            
        Returns:
            bool: True if enough bandwidth available, False otherwise
        """
        required_bandwidth = flow.get('bandwidth', 0)  # Get required bandwidth from flow
        
        # Check bandwidth availability for each edge in the path
        for i in range(len(path) - 1):
            current_node = path[i]
            next_node = path[i + 1]
            
            # Get current available bandwidth on the edge
            if not self.graph_list[flow['graph_index']].has_edge(current_node, next_node):
                return False
            
            edge = self.graph_list[flow['graph_index']][current_node][next_node]
            available_bandwidth = edge.get('bandwidth', 0)
            
            # Check if enough bandwidth is available
            if available_bandwidth < required_bandwidth:
                return False
            
        return True
    
    def allocate_resource(self, graph, flow, path):
        """
        Allocate bandwidth resources along the path for the flow
        
        Args:
            graph: NetworkX graph to allocate resources on
            flow: Flow dictionary containing bandwidth requirement
            path: List of nodes representing the path
        """
        required_bandwidth = flow.get('bandwidth', 0)
        
        # Reduce available bandwidth along each edge in the path
        for i in range(len(path) - 1):
            current_node = path[i] 
            next_node = path[i + 1]
            
            # Update the bandwidth on the edge
            if graph.has_edge(current_node, next_node):
                graph[current_node][next_node]['bandwidth'] -= required_bandwidth
            else:
                raise ValueError(f"Edge {current_node} -> {next_node} does not exist in graph")



