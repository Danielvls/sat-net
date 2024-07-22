# -*- coding: utf-8 -*-
# @Time    : 2024/6/30 18:13
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : utils.py

import time
import networkx as nx
import json
import os
from pathlib import Path


# decorator to measure the running time of a function
def timeit_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        print(f"Running {func.__name__}...", end='')
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Completed {func.__name__} in : {end_time - start_time:.3f} seconds")
        return result
    return wrapper


# decorator to save the graph after modification
def save_graph_after_modification(func):
    def wrapper(self, graph, idx, *args, **kwargs):
        result = func(self, graph, idx, *args, **kwargs)
        current_file = Path(__file__).resolve()
        project_root = current_file.parents[2]
        graph_path = project_root / "graphs" / f"graph{idx}.json"
        if graph:
            # save graph as json
            data = nx.node_link_data(graph)  # or nx.adjacency_data(graph)
            with open(graph_path, 'w') as f:
                json.dump(data, f, indent=4)
            # nx.write_graphml(graph, graph_path)
            print(f"Graph {idx} successfully saved after {func.__name__} modification. File path: {graph_path}")
        else:
            print(f"Warning: No graph was provided for saving at index {idx}.")
        return result
    return wrapper
