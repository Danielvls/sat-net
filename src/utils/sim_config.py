# -*- coding: utf-8 -*-
# @Time    : 2024/4/13 16:51
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : sim_config.py.py

# satellite network configure
num_orbit_planes = 7
num_sat_per_plane = 11

slot_num = 10
slot_size = 100

avg_duration = 1200
minimum_bandwidth, maximum_bandwidth = 300, 500
avg_bandwidth = (minimum_bandwidth + maximum_bandwidth) / 2
bandwidth_stddev = 0.01
# duration_stddev = 0.1

# snapshot step
time_step = 300   # 5min
