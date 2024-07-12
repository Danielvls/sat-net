# -*- coding: utf-8 -*-
# @Time    : 2024/6/29 10:18
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : test.py
import networkx as nx


def find_free_wavelengths(graph, node1, node2):
    # 检查链路是否存在
    if graph.has_edge(node1, node2):
        # 获取链路上的波长属性
        wavelengths = graph[node1][node2].get('wavelengths', {})
        # 找到所有状态为 "free" 的波长
        free_wavelengths = {wl: details for wl, details in wavelengths.items() if details['status'] == 'free'}
        return free_wavelengths
    else:
        print(f"No edge exists between {node1} and {node2}")
        return None


# 创建一个空的无向图
G = nx.Graph()

# 添加节点
G.add_node("Node1")
G.add_node("Node2")

# 添加链路及其波长属性
wavelengths = {f"wavelength_{i}": {"id": i, "status": "free" if i % 2 == 0 else "busy"} for i in range(1, 11)}
G.add_edge("Node1", "Node2", wavelengths=wavelengths)

# 使用函数找到Node1和Node2之间的空闲波长
free_wavelengths = find_free_wavelengths(G, "Node1", "Node2")
if free_wavelengths:
    print("Free wavelengths on the link between Node1 and Node2:")
    for wl, details in free_wavelengths.items():
        print(f"  {wl} with ID {details['id']} is currently {details['status']}")
else:
    print("No free wavelengths available or the link does not exist.")
