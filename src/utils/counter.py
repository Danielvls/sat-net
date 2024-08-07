# -*- coding: utf-8 -*-
# @Time    : 2024/4/23 13:22
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : counter.py
class Counter:
    def __init__(self):
        self.total_flows = 0
        self.count_switches = 0
        self.blocked_services = 0

    def increment_switches(self):
        self.count_switches += 1

    def increment_blocked_services(self):
        self.blocked_services += 1

    def get_blocked_rate(self):
        return self.blocked_services / self.total_flows * 100 if self.total_flows != 0 else 0
