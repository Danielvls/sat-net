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


def gen_topo():
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
    directory_path = './data/fac_sat_chain'
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
                    graph.add_edge(node_a, node_b, weight=distance)
                    # write in file
                    nx.write_graphml(graph, f"./graphs/graph{idx}.graphml")
                    print(f"edge {node_a} to {node_b} has added in to graph{idx}")
                else:
                    print("graph not exist")

            graph_path = f"./graphs/graph1.graphml"
            graph = nx.read_graphml(graph_path)
            draw_graph(graph, layout='grid')


def find_time_index(time_list, time_point):
    """使用二分查找找到最接近的时间索引"""
    idx = bisect_left(time_list, time_point)
    if idx < len(time_list) and time_list[idx] == time_point:
        return idx
    return None


# calculate betweenness centrality
def betweenness_centrality_cal():
    # load graph from GraphML
    graph_loaded = nx.read_graphml("./graphs/graph1.graphml")
    bet_centrality_values = nx.betweenness_centrality(graph_loaded)
    for _, bet_centrality_value in bet_centrality_values.items():
        print(bet_centrality_value)


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


    # for node in graph_loaded.nodes():
    #     sp = nx.shortest_path_length(graph_loaded, source=node)
    #     for target in graph_loaded.nodes():
    #         if target != node:
    #             if node in sp[target]:
    #                 sptotal = len(sp[target]) - 1
    #                 for path in nx.all_shortest_paths(graph_loaded, source=node, target=target):
    #                     path_length = len(path)
    #                     for i in range(path_length - 1):
    #                         u, v = path[i], path[i + 1]
    #                         if (u, v) in btwn_cen_values:
    #                             btwn_cen_values[(u, v)] += 1.0 / sptotal
    #                         if (v, u) in btwn_cen_values:
    #                             btwn_cen_values[(v, u)] += 1.0 / sptotal

    # # print edge betweenness
    # for edge, betweenness in btwn_cen_values.items():
    #     print(f"The betweenness centrality of edge {edge} is: {betweenness}")


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


if __name__ == "__main__":
    # gen_topo()
    # edge_betweenness_centrality()
    # betweenness_centrality_cal()
    add_fac_to_topo()
