# -*- coding: utf-8 -*-
# @Time    : 2024/4/23 13:22
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : counter.py
import threading

class Counter:
    _instance = None
    _lock = threading.Lock()  # 用于确保线程安全
    _initialized = False  # 私有的类属性，用于防止重复初始化

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Counter, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self.__class__._initialized:
            # 初始化计数器属性
            self.__class__._initialized = True  # 更新初始化状态
            self.total_flows = 0
            self.blocked_flows = 0
            self.link_usage = {}
            self.node_usage = {}
            self.user_points = []

    def increment_node_usage(self, node_id):
        if node_id in self.node_usage:
            self.node_usage[node_id] += 1
        else:
            self.node_usage[node_id] = 1

    def get_node_usage(self):
        return self.node_usage

    def get_total_cost(self, graph_list):
        # 初始化统计变量
        total_cost = 0  # 统计所有频隙的数量
        edge_count = 0
        greater_than_1_count = 0  # 统计 share_degree 大于 2 的频隙数量
        share_degree_equals_1_count = 0  # 统计 share_degree 等于 1 的边数量

        for index, graph in enumerate(graph_list):
            for edge in graph.edges(data=True):
                share_degree_list = edge[2].get('share_degree', [])
                for share_degree in share_degree_list:
                    edge_count += 1
                    if share_degree > 1:
                        greater_than_1_count += 1
                    if share_degree == 1:
                        share_degree_equals_1_count += 1
        total_cost += greater_than_1_count * 2 + share_degree_equals_1_count
        return total_cost


    def increase_link_usage(self, edge):
        u, v = edge
        sorted_edge = tuple(sorted((u, v)))  # (min(u, v), max(u, v))

        # initialize link usage if not exist
        if sorted_edge not in self.link_usage:
            self.link_usage[sorted_edge] = 0

        # increase link usage
        self.link_usage[sorted_edge] += 1

    def get_link_usage(self, edge):
        return self.link_usage.get(edge, 0)

    def get_link_utilization(self):
        """Calculate the link utilization rate."""
        sum_usage = 0
        for edge, usage in self.link_usage.items():
           sum_usage += usage
        max_capacity = len(self.link_usage) * 50 * 13

        if max_capacity == 0:
            return 0  # Avoid division by zero, return 0 if no capacity is set

        utilization_rate = sum_usage / max_capacity
        return utilization_rate

    def increment_user_point(self, lat, lon):
        self.user_points.append((lat, lon))

    def get_user_points(self):
        return self.user_points

    def reset_counter(self):
        self.total_flows = 0
        self.blocked_flows = 0
        self.link_usage = {}
        self.user_points = []


    def increment_blocked_flows(self):
        self.blocked_flows += 1


    def get_blocked_rate(self):
        return (self.blocked_flows / self.total_flows * 100) if self.total_flows != 0 else 0

