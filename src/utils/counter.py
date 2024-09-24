# -*- coding: utf-8 -*-
# @Time    : 2024/4/23 13:22
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : counter.py
class Counter:
    _instance = None
    _initialized = False  # 私有的类属性，用于防止重复初始化

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Counter, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self.__class__._initialized:
            # 初始化你的计数器属性
            self.count = 0
            self.total_flows = 0
            self.count_switches = 0
            self.blocked_flows = 0
            self.__class__._initialized = True  # 更新初始化状态
            self.node_usage = {}  # 用于存储每个节点的使用次数

    def increment_node_usage(self, node_id):
        if node_id in self.node_usage:
            self.node_usage[node_id] += 1
        else:
            self.node_usage[node_id] = 1

    def get_node_usage(self):
        return self.node_usage

    def increment_total_flows(self):
        self.total_flows += 1

    def increment_blocked_flows(self):
        self.blocked_flows += 1

    def increment_count_switches(self):
        self.count_switches += 1

    def get_blocked_rate(self):
        return (self.blocked_flows / self.total_flows * 100) if self.total_flows != 0 else 0

