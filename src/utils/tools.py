# -*- coding: utf-8 -*-
# @Time    : 2024/6/30 18:13
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : utils.py

import time
import networkx as nx
import json
import os
import pandas as pd
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

def approx_time(origin_times: list, reference_time_list: list):
    """Approximate times from origin_times to nearest times in reference_time_list."""
    try:
        # Convert origin times to datetime objects, truncating seconds and microseconds
        processed_times = []
        for time_str in origin_times:
            # Split at decimal point to remove microseconds
            time_str = time_str.split('.')[0]
            try:
                dt = datetime.strptime(time_str, '%d %b %Y %H:%M:%S')
                processed_times.append(dt)
            except ValueError as e:
                logger.error(f"Failed to parse time string: {time_str}")
                raise e
        
        # Approximate each time to nearest reference time
        approximated_times = set()  # Use set to avoid duplicates
        
        for orig_time in processed_times:
            # Find the closest time that's less than or equal to orig_time
            approx_time = None
            for ref_time in reference_time_list:
                if ref_time > orig_time:
                    break
                approx_time = ref_time
            
            # Only add if we found an approximation
            if approx_time is not None:
                approximated_times.add(approx_time)
            else:
                logger.warning(f"No approximation found for {orig_time}")
    
        result = sorted(list(approximated_times))

        return result
        
    except Exception as e:
        logger.error(f"Error in approx_time: {e}")
        raise e

def get_time_list():
    project_root = Path(__file__).resolve().parents[2]
    with open(project_root / 'data' / 'time_series.json', 'r') as f:
        time_data = json.load(f)
    time_series = [pd.to_datetime(t) for t in time_data]
    return time_series
