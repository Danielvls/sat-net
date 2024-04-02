from run_stk import *
import networkx as nx
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


if __name__ == "__main__":
    gen_topo()
