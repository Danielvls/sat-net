# -*- coding: utf-8 -*-
# @Time    : 2024/7/22 14:34
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : path_weight_calculator.py

import networkx as nx


class PathWeightCalculator:
    def __init__(self, graph, path, satellites, ground_stations):
        self.satellites = satellites
        self.ground_stations = ground_stations
        self.graph = graph
        self.path = path
        self.sigma_s_g = self.calculate_sigma_s_g()

    def calculate_time_varying_centrality(self, graph, edge, t, delta_t):
        S = self.satellites
        G = self.ground_stations
        sigma_e = sum(
            self.calculate_sigma_s_g_e(self.graph, s, g, edge, t) for s in S for g in G
        )

        if self.sigma_s_g == 0:
            return 0
        else:
            return sigma_e / self.sigma_s_g

    @staticmethod
    def calculate_sigma_s_g_e(self, graph, s, g, edge, t):
        paths = nx.all_shortest_paths(graph, source=s, target=g)
        count = sum(1 for path in paths if edge in zip(path, path[1:]))
        return count

    def calculate_sigma_s_g(self):
        sigma_s_g = sum(
            len(list(nx.all_shortest_paths(self.graph, source=s, target=g)))
            for s in self.satellites
            for g in self.ground_stations
        )
        return sigma_s_g

    def calculate_path_weight(self, path, alpha=0, beta=1):
        R_total = 0
        for i in range(len(path) - 1):
            edge = (path[i], path[i + 1])
            D_e = self.calculate_time_varying_centrality(i)
            L_e = self.calculate_path_load()
            R_e = alpha * D_e + beta / max(L_e, 1)
            R_total += R_e
        return R_total

    def calculate_path_load(self):
        load = 0
        for i in range(len(self.path) - 1):
            load += self.graph[self.path[i]][self.path[i + 1]]['bandwidth_usage']
        return load
