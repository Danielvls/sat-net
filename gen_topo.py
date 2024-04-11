from run_stk import *
import networkx as nx
import random
# import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def gen_topo():
    df = pd.read_csv('./data/satellite_distances.csv')
    df['Distance'] = df['Distance'].round(0)
    # print(df)  # 打印DataFrame的前几行以查看数据

    # group by satellite
    distance_group = df.groupby('SatellitePair')
    group_size = len(next(iter(distance_group.groups.values())))
    n = 1
    for i in range(1, group_size):
        nth_distance = distance_group.nth(n)
        print(nth_distance)

        # create graph
        G = nx.Graph()

        # add edge in G
        for index, row in nth_distance.iterrows():
            # extract node name
            nodes = row['SatellitePair'].split(' to ')
            node1, node2 = nodes[0], nodes[1]
            distance = row['Distance']

            # add weight
            G.add_edge(node1, node2, weight=distance)

        # write in file
        nx.write_graphml(G, f"./graphs/graph{i}.graphml")
    # return G
    # # 绘制图
    # plt.figure(figsize=(10, 8))
    # # 使用spring_layout进行布局计算，positions是每个节点的位置
    # positions = nx.spring_layout(G)
    # # 绘制节点
    # nx.draw_networkx_nodes(G, positions, node_size=500)
    # # 绘制边，可以根据需要添加edge_color或其他属性
    # nx.draw_networkx_edges(G, positions)
    # # 绘制节点标签
    # nx.draw_networkx_labels(G, positions)
    # # 如果你想显示边的权重
    # edge_labels = nx.get_edge_attributes(G, 'weight')
    # nx.draw_networkx_edge_labels(G, positions, edge_labels=edge_labels)
    # plt.title('Satellite Connection Topology')
    # plt.axis('off')  # 不显示坐标轴
    # plt.show()


def betweenness_centrality_cal():
    # load graph from GraphML
    G_loaded = nx.read_graphml("./graphs/graph1.graphml")
    bet_centrality_values = nx.betweenness_centrality(G_loaded)
    for _, bet_centrality_value in bet_centrality_values.items():
        print(bet_centrality_value)


def edge_betweenness_centrality():
    G_loaded = nx.read_graphml("./graphs/graph1.graphml")
    # btwn_cen_values = dict.fromkeys(G_loaded.edges(), 0.0)

    # randomly choose node
    nodes_list = list(G_loaded.nodes())
    start_node = random.choice(nodes_list)
    target_node = "Sat11"
    while target_node == start_node:
        start_node = random.choice(nodes_list)

    # all shortest path source from start node
    sp = nx.shortest_path_length(G_loaded, source=start_node)
    for target_node, hops in sp.items():
        if target_node != start_node:
            print(f"The shortest path length from {start_node} to {target_node} is {hops}")


    # for node in G_loaded.nodes():
    #     sp = nx.shortest_path_length(G_loaded, source=node)
    #     for target in G_loaded.nodes():
    #         if target != node:
    #             if node in sp[target]:
    #                 sptotal = len(sp[target]) - 1
    #                 for path in nx.all_shortest_paths(G_loaded, source=node, target=target):
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


if __name__ == "__main__":
    # gen_topo()
    # edge_betweenness_centrality()
    betweenness_centrality_cal()
