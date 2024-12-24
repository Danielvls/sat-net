def load_graphs(self):
    # Load all graphs and store them in a dictionary with their corresponding times
    for index, _ in enumerate(self.time_series):
        graph_file = self.graph_path / f"graph{index}.json"
        if graph_file.exists():
            try:
                with open(graph_file, 'r') as file:
                    data = json.load(file)
                    graph = nx.node_link_graph(data)
                    self.graph_list.append(graph)
            except json.JSONDecodeError as e:
                print(f"Error loading {graph_file}: {e}")
        else:
            print(f"File {graph_file} does not exist.")


def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # 地球半径，单位为公里
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def _generate_node_lists(graph):
    satellites = []
    facilities = []

    # Separate satellites and ground stations
    for node in graph.nodes():
        if 'Sat' in node:
            satellites.append(node)
        elif 'Fac' in node:
            facilities.append(node)

    return satellites, facilities

import networkx as nx

# 创建一个带权图
G = nx.Graph()

# 添加带权重的边
G.add_edge(1, 2, weight=4)
G.add_edge(2, 3, weight=5)
G.add_edge(3, 4, weight=6)
G.add_edge(4, 5, weight=7)

# 查找最短路径（示例：从节点 1 到节点 5）
path = nx.shortest_path(G, source=1, target=5, weight='weight')

# 计算路径的权重和
path_weight = sum(G[u][v]['weight'] for u, v in zip(path[:-1], path[1:]))

print(f"最短路径：{path}")
print(f"路径的权重总和：{path_weight}")
