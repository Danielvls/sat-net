# -*- coding: utf-8 -*-
# @Time    : 2024/7/14 15:32
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : flow_generator.py

import random
import networkx as nx
from pathlib import Path
import json
import pandas as pd
import math
from datetime import timedelta

# geometry  
import geopandas as gpd
from shapely.geometry import Point, Polygon, MultiPolygon
from fuzzywuzzy import process

# utils
from src.utils import Counter, get_time_list
import pycountry


class FlowGenerator:
    def __init__(self,  graph_list=None, avg_flow_num=None):
        # Initialize flow generator with the number of flows
        self.current_file = Path(__file__).resolve()
        self.project_root = self.current_file.parents[2]
        self.time_series = get_time_list()
        self.graph_path = self.project_root / 'graphs'
        self.counter = Counter()

        # get configuration
        self.avg_flow_num = avg_flow_num
        self.avg_duration = avg_duration
        self.minimum_bandwidth = minimum_bandwidth
        self.maximum_bandwidth = maximum_bandwidth
        self.avg_bandwidth = (self.minimum_bandwidth + self.maximum_bandwidth) / 2
        self.bandwidth_stddev = (self.maximum_bandwidth - self.minimum_bandwidth) / 6  # 假设99.7%的数据在范围内

        # initialize lists
        self.graph_list = graph_list
        self.flows = []

        # 初始化国家数据
        # self.country_data = self._load_country_data(self.project_root / 'data' / 'world_internet_user.csv')
        # # 加载国家边界数据
        # self.country_shapes = self._load_country_shapes(
        #     self.project_root / 'data' / 'ne_10m_admin_0_countries' / 'ne_10m_admin_0_countries.shp')

    def generate_flows_for_each_graph(self):
        # the number of flows is Poisson distributed
        k = 3  # k 越大，方差越小
        num_flows = self.avg_flow_num

        # 用于记录每个卫星节点作为起始节点的次数
        satellite_usage = {}

        # generate flows for each graph
        for index in range(len(self.graph_list)):
            graph = self.graph_list[index]
            satellite_coords = self._load_satellite_data(self.graph_path / f'graph{index}.json')

            # generate node lists for each graph
            satellites, facilities = self._generate_node_lists(graph)

            # 生成随机国家和随机点
            selected_points = self._select_countries_and_points(num_flows)

            for point in selected_points:
                # 找到最近的卫星
                nearest_satellite_id, distance_to_sat = self._find_nearest_satellite(point[0], point[1], satellite_coords)

                # 如果卫星在图中，使用该卫星作为起始节点
                if nearest_satellite_id in graph.nodes:
                    start_node = nearest_satellite_id
                else:
                    # 否则，随机选择一个卫星节点
                    start_node = random.choice(satellites)

                # 统计卫星节点的使用次数
                satellite_usage[start_node] = satellite_usage.get(start_node, 0) + 1


                # 目标节点随机选择一个地面站
                target_node = random.choice(facilities)


                # # 使用正态分布生成带宽
                # bandwidth = round(np.random.normal(self.avg_bandwidth, self.bandwidth_stddev), 2)
                # # 确保带宽在最小和最大带宽之间
                # bandwidth = max(min(bandwidth, self.maximum_bandwidth), self.minimum_bandwidth)

                # 使用平均持续时间
                duration = 900

                # 流信息
                flow = {
                    "graph_index": index,
                    "primary_path": None,
                    "backup_path": None,
                    "start_node": start_node,
                    "target_node": target_node,
                    # "bandwidth": bandwidth,
                    "duration": duration,
                    "random_point": point,
                    "distance_to_satellite": distance_to_sat
                }
                self.flows.append(flow)
        return self.flows

    def generate_flows_for_plotting(self, num_flows):
        # 用于记录每个卫星节点作为起始节点的次数
        # counter = Counter()

        current_file = Path(__file__).resolve()
        project_root = current_file.parents[2]
        graph_path = project_root / 'graphs'
        graph_file = graph_path / 'graph0.json'

        if graph_file.exists():
            try:
                with open(graph_file, 'r') as file:
                    graph_data = json.load(file)
                    graph = nx.node_link_graph(graph_data)
            except json.JSONDecodeError as e:
                print(f"Error loading {graph_file}: {e}")
                return  # 读取失败，直接返回
        else:
            print(f"File {graph_file} does not exist.")
            return  # 文件不存在，直接返回

        satellites_to_remove = ['Sat14', 'Sat23', 'Sat19', 'Sat29', 'Sat33', 'Sat39', 'Sat43', 'Sat49', 'Sat53', 'Sat58', 'Sat63', 'Sat68']  # 替换为您想移除的卫星ID

        # 从图中移除指定的卫星节点
        graph.remove_nodes_from(satellites_to_remove)

        satellite_coords = self._load_satellite_data(graph_file)

        # 为每个图生成节点列表
        satellites, facilities = self._generate_node_lists(graph)

        # 生成随机国家和随机点
        selected_points = self._select_countries_and_points(num_flows)
        print(len(selected_points))

        for point in selected_points:
            # 找到最近的卫星
            nearest_satellite_id, distance_to_sat = self._find_nearest_satellite(point[0], point[1], satellite_coords)

            # count
            # print("Country:", country, "Point:", point)
            self.counter.increment_user_point(point[0], point[1])

            # 如果卫星在图中，使用该卫星作为起始节点
            if nearest_satellite_id in graph.nodes:
                start_node = nearest_satellite_id
            else:
                # 否则，随机选择一个卫星节点
                start_node = random.choice(satellites)

            # 随机选择一个地面站作为目标节点
            target_node = random.choice(facilities)

            # 创建图的副本并移除其他地面站
            graph_copy = graph.copy()
            other_facilities = [node for node in facilities if node != target_node]
            graph_copy.remove_nodes_from(other_facilities)

            try:
                path = nx.shortest_path(graph_copy, source=start_node, target=target_node)
                # if len(path) > 3:
                #     continue  # 跳过这个流
            except nx.NetworkXNoPath:
                # 如果没有路径，处理异常，例如跳过这个流
                continue

            for node in path:
                self.counter.increment_node_usage(node)

    @staticmethod
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

    # @staticmethod
    # def _load_country_data(csv_file):
    #     # 读取CSV文件并准备数据
    #     data = pd.read_csv(csv_file, encoding='ISO-8859-1', header=None)
    #
    #     # 指定列名
    #     data.columns = ['Country', 'weights']  # 直接使用归一化的权重
    #
    #     # 将国家名称转换为小写并去除前后空格
    #     data['Country'] = data['Country'].str.lower().str.strip()
    #
    #     # 输出调试信息
    #     # print("Columns in country_data:", data.columns.tolist())
    #
    #     return data[['Country', 'weights']]

    def _select_countries_and_points(self, n):
        # Get the current file path and locate the project root directory
        current_file = Path(__file__).resolve()
        project_root = current_file.parents[2]

        # File paths
        file_path_city = project_root / 'data' / 'population_data' / 'worldcities.csv'
        file_path_internet = project_root / 'data' / 'population_data' / 'world_internet_user_origin.csv'

        # Load city data with geographic information and internet usage data
        city_data = pd.read_csv(file_path_city)
        internet_data = pd.read_csv(file_path_internet, encoding='ISO-8859-1')

        # Extract relevant columns: city, country, population, latitude, and longitude
        city_country_population = city_data[['city', 'country', 'population', 'lat', 'lng']].copy()

        # Extract internet usage information: country and internet usage percentage
        internet_usage = internet_data[['Country', '% of Population']].copy()

        # Rename columns for clarity
        internet_usage = internet_usage.rename(columns={'% of Population': 'InternetUsagePercentage'})
        city_country_population = city_country_population.rename(
            columns={
                'city': 'City',
                'country': 'Country',
                'population': 'Population',
                'lat': 'Latitude',
                'lng': 'Longitude'
            }
        )

        # Merge city population data with internet usage data
        merged_data = pd.merge(city_country_population, internet_usage, on='Country', how='left')

        # Drop rows with NaN values in Population or InternetUsagePercentage
        cleaned_data = merged_data.dropna(subset=['Population', 'InternetUsagePercentage']).copy()

        # Add a new column for the number of internet users
        cleaned_data['InternetUsers'] = cleaned_data['Population'] * (cleaned_data['InternetUsagePercentage'] / 100)

        sampled_data = cleaned_data.sample(n=n, weights='InternetUsers', replace=True)
        points = list(zip(sampled_data['Longitude'], sampled_data['Latitude']))

        return points

        # countries = random.choices(
        #     self.country_data['Country'].tolist(),
        #     weights=self.country_data['weights'].tolist(),
        #     k=n
        # )
        # points = []
        # for country in countries:
        #     # 标准化并预处理国家名称
        #     standardized_country = self._standardize_country_name(country)
        #     # 在 country_shapes 中查找标准化后的名称
        #     country_shape = self.country_shapes[self.country_shapes['standardized_name'] == standardized_country]
        #     if country_shape.empty:
        #         # 如果未找到，使用模糊匹配
        #         matched_country = self._get_best_match(standardized_country)
        #         if matched_country:
        #             country_shape = self.country_shapes[self.country_shapes['standardized_name'] == matched_country]
        #         else:
        #             country_shape = gpd.GeoDataFrame()
        #             print(f"未找到 {country} 的国家形状。使用随机全球点。")
        #     if country_shape.empty:
        #         # 使用随机全球点
        #         random_point = (random.uniform(-90, 90), random.uniform(-180, 180))
        #     else:
        #         # 从国家多边形中生成随机点
        #         polygon = country_shape.iloc[0]['geometry']
        #         if isinstance(polygon, MultiPolygon):
        #             # 随机选择一个多边形
        #             polygon = random.choice(polygon.geoms)
        #         random_point = self._generate_random_point_in_polygon(polygon)
        #     points.append(random_point)
        # return countries, points

    @staticmethod
    def _load_satellite_data(graph_file_path):
        # 加载卫星数据
        with open(graph_file_path, 'r') as f:
            satellite_data = json.load(f)
        # 提取卫星的经纬度坐标
        satellite_coords = []
        for node in satellite_data['nodes']:
            if 'latitude' in node and 'longitude' in node:
                satellite_coords.append({
                    'id': node['id'],
                    'latitude': node['latitude'],
                    'longitude': node['longitude']
                })
        return satellite_coords

    @staticmethod
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371  # 地球半径，单位为公里
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def _find_nearest_satellite(self, lat, lon, satellite_coords):
        nearest_sat = None
        min_distance = float('inf')
        for sat in satellite_coords:
            distance = self.haversine(lat, lon, sat['latitude'], sat['longitude'])
            if distance < min_distance:
                min_distance = distance
                nearest_sat = sat['id']
        return nearest_sat, min_distance

    def _load_country_shapes(self, shapefile_path):
        country_shapes = gpd.read_file(shapefile_path)
        # 将国家名称转换为小写并去除前后空格
        country_shapes['NAME'] = country_shapes['NAME'].str.lower().str.strip()
        # 添加标准化的国家名称列
        country_shapes['standardized_name'] = country_shapes['NAME'].apply(self._standardize_country_name)
        return country_shapes

    # @staticmethod
    # def _generate_random_point_in_polygon(polygon):
    #     minx, miny, maxx, maxy = polygon.bounds
    #     while True:
    #         random_point = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
    #         if polygon.contains(random_point):
    #             return random_point.x, random_point.y

    # def _get_best_match(self, country_name):
    #     choices = self.country_shapes['NAME'].tolist()
    #     best_match = process.extractOne(country_name, choices)
    #     if best_match[1] >= 80:  # 匹配度阈值，可根据需要调整
    #         return best_match[0]
    #     else:
    #         return None
    #
    # @staticmethod
    # def _standardize_country_name(country_name):
    #     try:
    #         # 尝试通过 pycountry 查找国家
    #         country = pycountry.countries.lookup(country_name)
    #         return country.name.lower()
    #     except LookupError:
    #         # 如果未找到，返回原始名称
    #         return country_name.lower()


