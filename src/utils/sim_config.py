# -*- coding: utf-8 -*-
# @Time    : 2024/4/13 16:51
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : sim_config.py.py

# satellite network configure
# T = 1584
# P = 72
# F = 11

# test topology
# T = 200
# P = 20
# F = 5

# test topology
T = 100
P = 10
F = 3

inc = 53
height = 6928
num_orbit_planes = int(P)
num_sat_per_plane = int(T / P)

# snapshot step
time_step = 300   # 5min

# flow configure
avg_flow_num = 10
# avg_duration = 1200
# minimum_bandwidth, maximum_bandwidth = 300, 500
# avg_bandwidth = (minimum_bandwidth + maximum_bandwidth) / 2
# bandwidth_stddev = 0.01
# duration_stddev = 0.1


