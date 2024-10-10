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
            self.node_usage = {}  # 用于存储每个节点的使用次数
            self.user_points = []  # 初始化一个列表来存储经纬度

    def increment_node_usage(self, node_id):
        if node_id in self.node_usage:
            self.node_usage[node_id] += 1
        else:
            self.node_usage[node_id] = 1

    def get_node_usage(self):
        return self.node_usage

    def increment_user_point(self, lat, lon):
        self.user_points.append((lat, lon))

    def get_user_points(self):
        return self.user_points

    def reset_counter(self):
        self.total_flows = 0
        self.blocked_flows = 0
        self.node_usage = {}  # 用于存储每个节点的使用次数
        self.user_points = []  # 初始化一个列表来存储经纬度

    def increment_blocked_flows(self):
        self.blocked_flows += 1


    def get_blocked_rate(self):
        return (self.blocked_flows / self.total_flows * 100) if self.total_flows != 0 else 0

