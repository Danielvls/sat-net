from RunSTK import *
import networkx as nx
# import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def gen_topo():
    df = pd.read_csv('./data/satellite_distances.csv')
    df['Distance'] = df['Distance'].round(0)
    # print(df)  # 打印DataFrame的前几行以查看数据

    # group by satellite
    n = 1
    nth_distance = df.groupby('SatellitePair').nth(n).reset_index()
    # print(nth_distance)

    # 创建图
    G = nx.Graph()

    # 向图中添加边
    for index, row in nth_distance.iterrows():
        # 假设SatellitePair列的格式是'SatX to SatY'
        # 需要从这个字符串中提取节点名
        nodes = row['SatellitePair'].split(' to ')
        node1, node2 = nodes[0], nodes[1]
        distance = row['Distance']

        # 添加边到图中，如果需要，还可以添加权重
        G.add_edge(node1, node2, weight=distance)
    # return G
    # 绘制图
    plt.figure(figsize=(10, 8))
    # 使用spring_layout进行布局计算，positions是每个节点的位置
    positions = nx.spring_layout(G)
    # 绘制节点
    nx.draw_networkx_nodes(G, positions, node_size=500)
    # 绘制边，可以根据需要添加edge_color或其他属性
    nx.draw_networkx_edges(G, positions)
    # 绘制节点标签
    nx.draw_networkx_labels(G, positions)
    # 如果你想显示边的权重
    edge_labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, positions, edge_labels=edge_labels)
    plt.title('Satellite Connection Topology')
    plt.axis('off')  # 不显示坐标轴
    plt.show()


if __name__ == "__main__":
    gen_topo()
