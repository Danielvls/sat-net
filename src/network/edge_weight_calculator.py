# -*- coding: utf-8 -*-
# @Time    : 2024/7/22 14:34
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : edge_weight_calculator.py


from collections import deque, defaultdict
from src.utils import find_time_indices, save_graph_after_modification


class EdgeWeightCalculator:
    def __init__(
            self,
            graph_list,
            time_series
    ):
        self.graph_list = graph_list
        self.time_series = time_series

    # def compute_dynamic_centrality(self):
    #
    #     t = self.flow['start_time']
    #     delta_t = self.flow['duration']
    #     total_paths_including_edge = 0
    #     total_paths = 0
    #
    #     # calculate the indices of the time series that are within the duration time of the flow
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

    @save_graph_after_modification
    def compute_static_centrality(self, graph, index, satellites, facilities):
        # S is the shortest path from s to g, P is the path, sigma is the number of nodes in S
        G = graph
        betweenness = defaultdict(float)

        # Iterating over all possible source and destination nodes
        for s in satellites:
            for g in facilities:
                if G.has_node(s) and G.has_node(g):
                    # Using Dijkstra's algorithm for weighted graphs
                    S, P, sigma, _ = self._single_source_shortest_path_basic(G, s, g)

                    # Accumulate edge betweenness values
                    betweenness = self._accumulate_edges(betweenness, S, P, sigma, s)

        # remove nodes to only return edges
        for node in list(betweenness.keys()):
            if isinstance(node, tuple) and len(node) == 2:
                continue
            del betweenness[node]

        # The centrality value of the normalized edge
        betweenness = self._rescale_e(
            betweenness, len(G), normalized=True, directed=G.is_directed()
        )

        # The computed centrality value is written to the edge property of the graph
        for edge in G.edges():
            # Set centrality to infinity for edges connecting facilities
            if edge[0] in facilities or edge[1] in facilities:
                G[edge[0]][edge[1]]['betweenness'] = float('inf')
            else:
                # Determines whether edges exist in the betweenness dictionary, and defaults to 0 if they do not
                G[edge[0]][edge[1]]['betweenness'] = betweenness.get((edge[0], edge[1]), 0.0)

        return G

    # def compute_dynamic_centrality(self):
    #     t = self.time_series[self.flow['graph_index']]
    #     delta_t = self.flow['duration']
    #     indices = find_time_indices(self.time_series, t, delta_t)
    #     dynamic_centrality = defaultdict(float)
    #     total_interval_time = len(indices)
    #
    #     for index in indices:
    #         G = self.graph_list[index]
    #         betweenness = defaultdict(float)
    #
    #         # Iterating over all possible source and destination nodes
    #         for s in self.satellites:
    #             for g in self.facilities:
    #                 if G.has_node(s) and G.has_node(g):
    #                     # Using Dijkstra's algorithm for weighted graphs
    #                     S, P, sigma, _ = self._single_source_shortest_path_basic(G, s)
    #
    #                     # Accumulate edge betweenness values
    #                     betweenness = self._accumulate_edges(betweenness, S, P, sigma, s)
    #
    #         for s in G:  # remove nodes to only return edges
    #             del betweenness[s]
    #
    #         betweenness = self._rescale_e(
    #             betweenness, len(G), normalized=True, directed=G.is_directed()
    #         )
    #
    #         # Update dynamic_centrality
    #         for edge in betweenness:
    #             dynamic_centrality[edge] += betweenness[edge]
    #
    #     # Normalize the betweenness values for this time slice
    #     for edge in dynamic_centrality:
    #         dynamic_centrality[edge] /= total_interval_time
    #
    #     # print(self.edge, ': ', dynamic_centrality[(self.edge[0], self.edge[1])])
    #     return dynamic_centrality[(self.edge[0], self.edge[1])]

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
        # S: 从节点 s 可到达的所有节点集合，按照从终点到起点的顺序排列。
        # P: 一个字典，P[w] 表示从 s 到 w 的所有最短路径的前驱节点集合。
        # sigma: 一个字典，sigma[w] 表示从起点 s 到节点 w 的最短路径的总数。

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
    def _single_source_shortest_path_basic(G, s, g):
        # find shortest paths from s to all other nodes in G
        S = []  # source
        P = {}  # previous node

        #
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

    def calculate_edge_weight(self):
        R_total = 0
        D_e = self.compute_dynamic_centrality()
        # L_e = self.calculate_edge_load(edge)
        # D_e = 0
        # L_e = 0
        # R_e = alpha * D_e + beta / max(L_e, 1)
        # R_total += R_e
        return D_e

