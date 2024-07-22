# -*- coding: utf-8 -*-
# @Time    : 2024/4/13 16:51
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : old_traffic_generator.py

import random
import networkx as nx
from sim_config import *
import numpy as np
import pandas as pd
from scipy.stats import poisson
from datetime import timedelta
import counter

# 假设光速为光在光纤中的速度，单位为千米/秒
SPEED_OF_LIGHT = 300000  # 约 2/3 * 真空中的光速
counter = counter.Counter()


def switch_path(graph, service):
    start_node = service['start_node']
    target_node = service['target_node']
    package_size = service['package_size']

    # 计算新的路径
    primary_path, backup_path = calculate_paths(graph, start_node, target_node)

    # 检查新路径的带宽是否足够
    if all(check_path_bandwidth(graph, path, package_size) for path in (primary_path,  backup_path)):
        # 更新带宽
        for path in (primary_path, backup_path):
            update_bandwidth(graph, path, package_size)
        # print(f"Graph updated for service {service['service_id']}")
        service['primary_path'] = primary_path
        service['backup_path'] = backup_path
        counter.increment_switches()
    else:
        counter.increment_blocked_services()
        service['primary_path'] = None
        service['backup_path'] = None


def calculate_transmission_delay(graph, path):
    total_distance = sum(graph[u][v]['weight'] for u, v in zip(path[:-1], path[1:]))
    return total_distance / SPEED_OF_LIGHT


def find_time_indices(start_time, delay, time_series):
    end_time = start_time + timedelta(seconds=delay)
    indices = []
    for i, time in enumerate(time_series):
        if start_time <= time <= end_time:
            indices.append(i)
    return indices


def calculate_paths(graph, start_node, target_node, existing_path=None):
    # Calculate primary and backup paths for a service
    primary_path = calculate_shortest_path(graph, start_node, target_node) if not existing_path else existing_path
    backup_path = calculate_backup_path(graph, start_node, target_node, primary_path)
    return primary_path, backup_path


def update_graphs_for_service(index, service, graph_dict):
    # Process service updates across time-series graphs
    start_time = pd.to_datetime(graph_dict[index]['time'])
    time_list = [graph_dict[index]['time'] for index in graph_dict if 'time' in graph_dict[index]]
    indices = find_time_indices(start_time, service['delay'], time_list)
    # print(f"service {service['service_id']} affact {indices}")

    # Distribute the service across all graphs it spans.
    for index in indices:
        graph_info = graph_dict.get(index)
        # print(f"this is index:{index}!")
        if graph_info:
            graph = graph_info['graph']
            primary_path = service.get('primary_path')
            backup_path = service.get('backup_path')
            package_size = service.get('package_size')
            start_node = service.get('start_node')
            target_node = service.get('target_node')
            service_id = service.get('service_id')

            # check if the service has the path value
            if not (primary_path and backup_path):
                # print(f"assign path to service{service_id} at graph {index}!")
                primary_path, backup_path = calculate_paths(graph, start_node, target_node, primary_path)
                service['primary_path'] = primary_path
                service['backup_path'] = backup_path

            # check if the path is valid if the path is not valid means no connection or no bandwidth
            if not all(check_path_bandwidth(graph, path, package_size) for path in (primary_path, backup_path)):
                # if the last satellite can't connect the facility the path need to switch
                switch_path(graph, service)


def check_path_bandwidth(graph, path, package_size):
    if path is None:
        print("Attempted to check bandwidth for a None path.")
        return False
    for u, v in zip(path[:-1], path[1:]):
        if not graph.has_edge(u, v):
            return False  # 如果边不存在，返回False
        if 'bandwidth' not in graph.edges[u, v] or graph.edges[u, v]['bandwidth'] < package_size:
            return False  # 如果任何边的带宽不足，返回False
    return True  # 所有边的带宽都足够


def update_bandwidth(graph, path, package_size):
    for u, v in zip(path[:-1], path[1:]):
        if 'bandwidth' in graph[u][v]:
            graph[u][v]['bandwidth'] -= package_size
            if graph[u][v]['bandwidth'] < 0:
                graph[u][v]['bandwidth'] = 0


def calculate_shortest_path(graph, start_node, target_node):
    try:
        path = nx.shortest_path(graph, source=start_node, target=target_node)
        return path
    except nx.NetworkXNoPath:
        return None


def calculate_backup_path(graph, start_node, target_node, shortest_path):
    try:
        graph_copy = graph.copy()

        second_last_node = shortest_path[-2]

        if len(shortest_path) > 3:
            for node in shortest_path[1:-2]:
                graph_copy.remove_node(node)

        # mantain the second last node
        path = nx.shortest_path(graph_copy, source=start_node, target=second_last_node)
        path.append(target_node)
        return path
    except nx.NetworkXNoPath:
        return None


def generate_traffic(graph_dict):
    # Process service updates across time-series graphs
    # start_time = pd.to_datetime(graph_dict[0]['time'])
    # print(f"start at {start_time}!")
    # indices = find_time_indices(start_time, service['delay'], time_series)

    # generate services for each graph
    for index in range(len(graph_dict)):
        graph_info = graph_dict.get(index)
        # print(f"this is index:{index}!")
        if graph_info:
            graph = graph_info['graph']
            services = {}
            # each graph generate certain amount of services
            for i in range(num_services):
                # sort the node list into sat and fac
                satellites, ground_stations = generate_node_lists(graph)

                # generate services
                service_id = i
                start_node = random.choice(satellites)
                target_node = random.choice(ground_stations)
                # while target_node == start_node:
                #     target_node = random.choice(nodes_list)
                package_size = round(random.uniform(0, 1024), 2)
                # delay = calculate_transmission_delay(graph, primary_path)
                delay = round(random.uniform(1000, 5000), 2)

                services[service_id] = {
                    "service_id": service_id,
                    "primary_path": None,
                    "backup_path": None,
                    "start_node": start_node,
                    "target_node": target_node,
                    "package_size": package_size,
                    "delay": delay
                }

                # push service into network
                update_graphs_for_service(index, services[service_id], graph_dict)

                counter.increment_total_services()

    print(f"switch {counter.count_switches} times!")
    print(f"total services number is {counter.total_services}!")
    print(f"total blocked services number is {counter.blocked_services}!")
    print(f"blocked rate is {counter.get_blocked_rate()}!")


def generate_node_lists(graph):
    satellites = []
    ground_stations = []

    # 假设卫星节点的名称以 'Sat' 开头，地面站节点的名称以 'Fac' 开头
    for node in graph.nodes():
        if 'Sat' in node:
            satellites.append(node)
        elif 'Fac' in node:
            ground_stations.append(node)

    return satellites, ground_stations


def run():
    # 读取时间序列数据从 CSV 文件
    time_df = pd.read_csv("data/time_series.csv")
    time_series = pd.to_datetime(time_df['Time Series'])

    # 创建一个字典来存储图和对应的时间
    graph_dict = {}

    # Load all graphs and store them in a dictionary with their corresponding times
    for index in range(len(time_series)):
        graph_path = f"./graphs/graph{index}.graphml"
        graph = nx.read_graphml(graph_path)
        graph_dict[index] = {'graph': graph, 'time': time_series[index]}

    service_example = {
        'service_id': 1,
        'start_time': '2020-08-01 16:10:00',
        'primary_path': ['Sat23', 'Sat22', 'Sat21', 'Sat28', 'Sat38', 'MyFacility'],
        'backup_path': ['Sat23', 'Sat33', 'Sat32', 'Sat31', 'Sat38', 'MyFacility'],
        'start_node': 'Sat23',
        'target_node': 'MyFacility',
        'package_size': 430.18,
        'delay': 2000
    }
    service_example2 = {
        'service_id': 2,
        'start_time': '2020-08-01 16:10:00',
        'primary_path': ['Sat17', 'Sat27', 'Sat37', 'MyFacility'],
        'backup_path': ['Sat17', 'Sat18', 'Sat28', 'Sat38', 'MyFacility'],
        'start_node': 'Sat17',
        'target_node': 'MyFacility',
        'package_size': 430.18,
        'delay': 2000
    }
    generate_traffic(graph_dict)
    # update_graphs_for_service(service_example, graph_dict)

    # # generate traffic by using dictionary
    # for index, graph_info in graph_dict.items():
    #     print(f"the {index}-th graph service at time {graph_info['time']}:")
    #     generate_traffic(graph_info['graph'])

    # # Topology-by-topology read
    # for index in range(len(time_series)):
    #     # load graph from GraphML
    #     graph = nx.read_graphml(f"./graphs/graph{index}.graphml")
    #     print(f"the {index}-th graph service:")
    #     generate_traffic(graph)


if __name__ == "__main__":
    run()

