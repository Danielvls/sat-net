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
from datetime import timedelta, datetime
from src.utils.logger import Logger

logger = Logger().get_logger()

# find time indices in the time series that are within the duration time of the flow
def find_time_indices(time_series, start_time, duration):
    end_time = start_time + timedelta(seconds=duration)
    indices = []
    for i, t in enumerate(time_series):
        if start_time <= t <= end_time:
            indices.append(i)
    return indices


# # decorator to measure the running time of a function
# def timeit_decorator(func):
#     def wrapper(*args, **kwargs):
#         start_time = time.time()
#         logger.info(f"Running {func.__name__}...", end='')
#         result = func(*args, **kwargs)
#         end_time = time.time()
#         logger.info(f"Completed {func.__name__} in : {end_time - start_time:.3f} seconds...", end="")
#         return result
#     return wrapper


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
                logger.debug(f"trying to dump {data} to {graph_path}")
                json.dump(data, f, indent=4)
            # nx.write_graphml(graph, graph_path)
            logger.info(f"Graph {idx} successfully saved after {func.__name__} modification. File path: {graph_path}")
        else:
            logger.warning(f"Warning: No graph was provided for saving at index {idx}.")
        return result
    return wrapper

# truncate the time string to remove microseconds or smaller units
def truncate_times(chain_times, format_str="%d %b %Y %H:%M:%S") -> list:
    dt_times = []
    for time_str in chain_times:
        if '.' in time_str:
            time_str = time_str[:time_str.rfind('.')]
        dt_time = datetime.strptime(time_str, format_str)
        dt_times.append(dt_time)
    return dt_times

