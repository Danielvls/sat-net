# traffic_generator.py
import random
import networkx as nx
from sim_config import *


def calculate_shortest_path(graph, start_node, target_node):
    try:
        path = nx.shortest_path(graph, source=start_node, target=target_node)
        return path
    except nx.NetworkXNoPath:
        return None


# 放入节点输入队列
# def put_service_in_queue(env, node_name, node_instances, service_id, service, simulation_duration):
#     # 等待时间生成
#     wait_time = random.uniform(0, simulation_duration-5)
#     yield env.timeout(wait_time)
#
#     service["time"] = env.now
#     # print(f"service {service_id} start from {node_name} at time {env.now:.2f}")
#     node_instances[node_name].in_queue.append(service_id)


def generate_traffic():
    # load graph from GraphML
    G_loaded = nx.read_graphml("./graphs/graph1.graphml")

    # get node list
    nodes_list = list(G_loaded.nodes())

    # generate service
    services = {}
    for i in range(num_services):
        # id
        service_id = i

        # randomly choose node
        start_node = random.choice(nodes_list)
        target_node = random.choice(nodes_list)
        while target_node == start_node:
            target_node = random.choice(nodes_list)
        this_node = start_node

        package_size = random.uniform(0, 0.3)  # 0-2MByte

        # 计算最短路径
        path = calculate_shortest_path(G_loaded, start_node, target_node)
        if path:

            # 获取路径的下一个节点
            next_node = path[1] if len(path) > 1 else None
            # next_node = None
            # 添加业务信息到嵌套字典
            services[service_id] = {"service_id": service_id, "path": path,
                                    "start_node": start_node, "target_node": target_node,
                                    "this_node": this_node, "next_node": next_node,
                                    "package_size": package_size}
        else:
            print(f"No path found for service {service_id}")
    for service_id, service in services.items():
        print(f"the {service_id}-th service: {services[service_id]}")
    return services


if __name__ == "__main__":
    generate_traffic()
