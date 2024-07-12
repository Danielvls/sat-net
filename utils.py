# -*- coding: utf-8 -*-
# @Time    : 2024/6/30 18:13
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : utils.py

import time
import networkx as nx


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
        graph_path = f"./graphs/graph{idx}.graphml"
        if graph:
            nx.write_graphml(graph, graph_path)
            print(f"Graph {idx} has been updated and saved.")
        else:
            print(f"Warning: No graph was provided for saving at index {idx}.")
        return result
    return wrapper
