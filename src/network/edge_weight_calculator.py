# -*- coding: utf-8 -*-
# @Time    : 2024/7/22 14:34
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : edge_weight_calculator.py

import networkx as nx
from collections import deque, defaultdict
from src.network.flow_controller import find_time_indices
from src.utils import find_time_indices


class EdgeWeightCalculator:
    def __init__(
            self,
            graph_dict,
            edge,
            path,
            flow,
            time_series,
            satellites,
            facilities
    ):
        self.satellites = satellites
        self.facilities = facilities
        self.graph_dict = graph_dict
        self.edge = edge
        self.path = path
        self.flow = flow
        self.time_series = time_series

    # def compute_dynamic_centrality(self):
    #
    #     t = self.flow['start_time']
    #     delta_t = self.flow['delay']
    #     total_paths_including_edge = 0
    #     total_paths = 0
    #
    #     # calculate the indices of the time series that are within the delay time of the flow
    #     indices = find_time_indices(self.time_series, t, delta_t)
    #
    #     for index in indices:
    #         current_graph = self.graph_dict.get(index, None)
    #         if current_graph is None:
    #             continue
    #
    #         #
    #         graph = nx.Graph(current_graph)
    #
    #         #
    #         for s in self.satellites:
    #             for g in self.facilities:
    #                 if graph.has_node(s) and graph.has_node(g):
    #                     all_paths = list(nx.all_shortest_paths(graph, source=s, target=g))
    #                     paths_including_edge = [path for path in all_paths if self.edge in zip(path[:-1], path[1:])]
    #
    #                     total_paths_including_edge += len(paths_including_edge)
    #                     total_paths += len(all_paths)
    #     if total_paths == 0:
    #         return 0  # if there is no path, return 0
    #     dynamic_centrality = (total_paths_including_edge / total_paths) / delta_t
    #     return dynamic_centrality

    def compute_dynamic_centrality(self):
        t = self.time_series[self.flow['graph_index']]
        delta_t = self.flow['delay']
        indices = find_time_indices(self.time_series, t, delta_t)
        dynamic_centrality = defaultdict(float)
        total_interval_time = len(indices)

        for index in indices:
            G = self.graph_dict.get(index, None)['graph']
            betweenness = defaultdict(float)

            # Iterating over all possible source and destination nodes
            for s in self.satellites:
                for g in self.facilities:
                    if G.has_node(s) and G.has_node(g):
                        # Using Dijkstra's algorithm for weighted graphs
                        S, P, sigma, _ = self._single_source_shortest_path_basic(G, s)

                        # Accumulate edge betweenness values
                        betweenness = self._accumulate_edges(betweenness, S, P, sigma, s)

            for s in G:  # remove nodes to only return edges
                del betweenness[s]

            betweenness = self._rescale_e(
                betweenness, len(G), normalized=True, directed=G.is_directed()
            )

            # Update dynamic_centrality
            for edge in betweenness:
                dynamic_centrality[edge] += betweenness[edge]

        # Normalize the betweenness values for this time slice
        for edge in dynamic_centrality:
            dynamic_centrality[edge] /= total_interval_time

        # print(self.edge, ': ', dynamic_centrality[(self.edge[0], self.edge[1])])
        return dynamic_centrality[(self.edge[0], self.edge[1])]

    @staticmethod
    def _rescale_e(betweenness, n, normalized, directed=False, k=None):
        if normalized:
            if n <= 1:
                scale = None  # no normalization b=0 for all nodes
            else:
                scale = 1 / (n * (n - 1))
        else:  # rescale by 2 for undirected graphs
            if not directed:
                scale = 0.5
            else:
                scale = None
        if scale is not None:
            if k is not None:
                scale = scale * n / k
            for v in betweenness:
                betweenness[v] *= scale
        return betweenness

    @staticmethod
    def _accumulate_edges(betweenness, S, P, sigma, s):
        delta = dict.fromkeys(S, 0)
        while S:
            w = S.pop()
            coeff = (1 + delta[w]) / sigma[w]
            for v in P[w]:
                c = sigma[v] * coeff
                if (v, w) not in betweenness:
                    betweenness[(w, v)] += c
                else:
                    betweenness[(v, w)] += c
                delta[v] += c
            if w != s:
                betweenness[w] += delta[w]
        return betweenness

    @staticmethod
    def _single_source_shortest_path_basic(G, s):
        S = []
        P = {}
        for v in G:
            P[v] = []
        sigma = dict.fromkeys(G, 0.0)  # sigma[v]=0 for v in G
        D = {}
        sigma[s] = 1.0
        D[s] = 0
        Q = deque([s])
        while Q:  # use BFS to find shortest paths
            v = Q.popleft()
            S.append(v)
            Dv = D[v]
            sigmav = sigma[v]
            for w in G[v]:
                if w not in D:
                    Q.append(w)
                    D[w] = Dv + 1
                if D[w] == Dv + 1:  # this is a shortest path, count paths
                    sigma[w] += sigmav
                    P[w].append(v)  # predecessors
        return S, P, sigma, D


    # @staticmethod
    # def calculate_sigma_s_g_e(graph, s, g, edge, t):
    #     paths = nx.all_shortest_paths(graph, source=s, target=g)
    #     count = sum(1 for path in paths if edge in zip(path, path[1:]))
    #     return count

    def calculate_edge_weight(self):
        R_total = 0
        D_e = self.compute_dynamic_centrality()
        # L_e = self.calculate_edge_load(edge)
        # D_e = 0
        # L_e = 0
        # R_e = alpha * D_e + beta / max(L_e, 1)
        # R_total += R_e
        return D_e

    # def calculate_path_load(self):
    #     load = 0
    #     for i in range(len(self.path) - 1):
    #         load += self.graph[self.path[i]][self.path[i + 1]]['bandwidth_usage']
    #     return load



def main():
    edge_weight_calculator = EdgeWeightCalculator()
    edge_weight_calculator.calculate_edge_weight()


if __name__ == "__main__":
    main()
