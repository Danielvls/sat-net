# -*- coding: utf-8 -*-
# @Time    : 2024/4/13 16:51
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : gen_topo.py

from run_stk import *
import networkx as nx
import random
from bisect import bisect_left
# import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import functools


def save_graph_after_modification(func):
    @functools.wraps(func)
    def wrapper(graph, idx, *args, **kwargs):
        # 执行传入的函数
        result = func(graph, idx, *args, **kwargs)

        # 构建图的文件路径
        graph_path = f"./graphs/graph{idx}.graphml"

        # 保存图到文件
        if graph:  # 确保图不为空
            nx.write_graphml(graph, graph_path)
            print(f"Graph {idx} has been updated and saved.")
        else:
            print(f"Warning: No graph was provided for saving at index {idx}.")

        return result

    return wrapper


@save_graph_after_modification
def add_bandwidth_to_edges(graph, idx):
    if graph:
        for u, v in graph.edges():
            graph[u][v]['bandwidth'] = 1024 * 10
    else:
        print(f"Warning: No graph found to update at index {idx}.")


@save_graph_after_modification
def add_node_betweenness_centrality(graph, idx):
    if graph:
        graph = betweenness_centrality_cal(graph)
    else:
        print(f"Warning: No graph found to update at index {idx}.")


def add_sat_to_topo():
    # generate sat links
    sat_df = pd.read_csv('./data/satellite_distances.csv')
    # sat_df['Distance'] = sat_df['Distance'].round(0)
    # print(sat_df)  # 打印DataFrame的前几行以查看数据

    # group by satellite
    distance_group = sat_df.groupby('SatellitePair')
    group_size = len(next(iter(distance_group.groups.values())))

    # write in files according to time slice
    for i in range(0, group_size):
        nth_distance = distance_group.nth(i)
        # print(nth_distance)

        # create graph
        graph = nx.Graph()

        # add edge in graph
        for index, row in nth_distance.iterrows():
            # extract node name
            nodes = row['SatellitePair'].split(' to ')
            node1, node2 = nodes[0], nodes[1]
            distance = row['Distance']

            # add weight
            graph.add_edge(node1, node2, weight=distance)

    # sat_df = pd.read_csv('./data/satellite_distances.csv')

        # write in file
        nx.write_graphml(graph, f"./graphs/graph{i}.graphml")


# add facility to topo
def add_fac_to_topo():
    directory_path = 'data/fac_sat_chains'
    time_df = pd.read_csv("./data/time_series.csv")
    time_list = pd.to_datetime(time_df['Time Series']).tolist()

    # Iterate over each file in the directory
    for filename in os.listdir(directory_path):
        if filename.endswith(".csv"):  # Ensure we are processing CSV files
            filepath = os.path.join(directory_path, filename)
            # Parse node names from the filename
            node_a, node_b = filename[:-4].split(' To ')

            # Read the file content
            df = pd.read_csv(filepath)

            # Iterate over each row in the DataFrame
            for index, row in df.iterrows():
                chain_time = pd.to_datetime(row['Time'])  # 假设时间列名为'Time'
                distance = row['Distance']  # 假设距离列名为'Distance'

                # 找到时间对应的图索引
                idx = find_time_index(time_list, chain_time)
                print(idx)
                # Read the graph for the found index, create if does not exist
                graph_path = f"./graphs/graph{idx}.graphml"
                if os.path.exists(graph_path):
                    graph = nx.read_graphml(graph_path)
                    if not graph.has_node(node_a):
                        graph.add_node(node_a)
                    if not graph.has_node(node_b):
                        graph.add_node(node_b)
                    graph.add_edge(node_a, node_b, weight=distance, bidirectional=True)
                    # write in file
                    nx.write_graphml(graph, f"./graphs/graph{idx}.graphml")
                    print(f"edge {node_a} to {node_b} has added in to graph{idx}")
                else:
                    print("graph not exist")

            # graph_path = f"./graphs/graph1.graphml"
            # graph = nx.read_graphml(graph_path)
            # draw_graph(graph, layout='grid')


def find_time_index(time_list, time_point):
    """使用二分查找找到最接近的时间索引"""
    idx = bisect_left(time_list, time_point)
    if idx < len(time_list) and time_list[idx] == time_point:
        return idx
    return None


# calculate betweenness centrality
def betweenness_centrality_cal(graph):
    # 计算图的介数中心性
    bet_centrality_values = nx.betweenness_centrality(graph)

    # 将介数中心性值存储为节点的属性
    for node, bet_centrality_value in bet_centrality_values.items():
        graph.nodes[node]['betweenness_centrality'] = bet_centrality_value
        print(f"Node {node}: {bet_centrality_value}")

    # 返回修改后的图
    return graph


def edge_betweenness_centrality():
    graph_loaded = nx.read_graphml("./graphs/graph1.graphml")
    # btwn_cen_values = dict.fromkeys(graph_loaded.edges(), 0.0)

    # randomly choose node
    nodes_list = list(graph_loaded.nodes())
    start_node = random.choice(nodes_list)
    target_node = "Sat11"
    while target_node == start_node:
        start_node = random.choice(nodes_list)

    # all shortest path source from start node
    sp = nx.shortest_path_length(graph_loaded, source=start_node)
    for target_node, hops in sp.items():
        if target_node != start_node:
            print(f"The shortest path length from {start_node} to {target_node} is {hops}")


def add_betweenness_to_topo(time_series):
    print(time_series)
    for index in range(len(time_series)):
        # load graph from GraphML
        graph = nx.read_graphml(f"./graphs/graph{index}.graphml")
        print(f"the {index}-th graph service:")
        for u, v in graph.edges():
            graph[u][v]['bandwidth'] = 1024 * 10


def draw_graph(graph, layout='spring'):
    """
    绘制给定的networkx图，支持不同的布局方式。

    Parameters:
    - graph (networkx.Graph): 要绘制的图。
    - layout (str): 布局类型，支持 'spring'（弹簧布局）和 'grid'（网格布局）。
    """
    plt.figure(figsize=(10, 8))
    if layout == 'grid':
        # 创建一个近似的网格布局
        side = int(np.sqrt(len(graph.nodes()))) + 1
        positions = {node: (i % side, -i // side) for i, node in enumerate(graph.nodes())}
    else:
        # 默认使用spring_layout
        positions = nx.spring_layout(graph)

    # 绘制图形的节点、边、节点标签和边的标签（权重）
    nx.draw_networkx_nodes(graph, positions, node_size=500, node_color='skyblue')
    nx.draw_networkx_edges(graph, positions)
    nx.draw_networkx_labels(graph, positions, font_size=12, font_family='sans-serif')

    # 如果边有权重属性，显示边的权重
    edge_labels = nx.get_edge_attributes(graph, 'weight')
    if edge_labels:
        nx.draw_networkx_edge_labels(graph, positions, edge_labels=edge_labels, font_color='red')

    plt.title('Satellite Connection Topology')
    plt.axis('off')  # 隐藏坐标轴
    plt.show()


def gen_topo():
    time_df = pd.read_csv("./data/time_series.csv")
    time_series = time_df['Time Series']
    # add_sat_to_topo()
    # add_fac_to_topo()
    for index in range(len(time_series)):
        graph_path = f"./graphs/graph{index}.graphml"
        if os.path.exists(graph_path):
            graph = nx.read_graphml(graph_path)
            add_bandwidth_to_edges(graph, index)
            add_node_betweenness_centrality(graph, index)
        else:
            print(f"Graph file {graph_path} does not exist for index {index}")

    # add_betweenness_to_topo(time_series)


if __name__ == "__main__":
    gen_topo()
