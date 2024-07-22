# -*- coding: utf-8 -*-
# @Time    : 2024/6/29 10:18
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : test.py
import networkx as nx

G = nx.cycle_graph(50)
paths = list(nx.shortest_simple_paths(G, 0, 3))[:3]
print(paths)
