# -*- coding: utf-8 -*-
# @Time    : 2024/7/14 15:41
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : main.py


from src.stk import STKManager
# from plot.satellite_visualizer import SatelliteVisualizer
from src.utils import *
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from src.utils.logger import Logger
from src.utils.tools import get_graph_list
from src.network import FlowGenerator, FlowController

logger = Logger().get_logger()

def main():
    # # --------------------------------------------------------------------------------------
    # # 调试部分
    # # --------------------------------------------------------------------------------------
    # Check if graphs folder exists and contains graph files
    project_root = Path(__file__).resolve().parent
    graphs_dir = project_root / 'graphs'
    
    if graphs_dir.exists() and any(graphs_dir.glob('graph*.json')):
        # If graph files exist, generate graph list
        logger.info("Graph files found, generating graph list...")
        # graph_list = get_graph_list(graphs_dir)
    else:
        # Create graphs directory if it doesn't exist
        graphs_dir.mkdir(parents=True, exist_ok=True)
        logger.info("No graph files found, running STK simulation first...")
        # Initialize STK Manager
        manager = STKManager()
        manager.launch_stk()
        manager.attach_to_application()
        # manager.load_scenario('D:/STKScenario/200/200sat.sc',
        #                       "1 Aug 2020 16:00:00", "1 Aug 2020 16:30:00")
        manager.create_scenario("1 Aug 2020 16:00:00", "1 Aug 2020 17:00:00")
        manager.create_constellation("DeltaConstellation")
        manager.create_facilities()
        manager.get_sat_access(constraint=True)
        manager.get_fac_access()
        manager.get_sat_lla()
        manager.save_graph_data()
        

    
    # # # Initialize flow generator with the number of flows
    # flow_generator = FlowGenerator(graph_list)
    # flows = flow_generator.generate_flows_for_each_graph()

    # # process flows
    # flow_controller = FlowController(flows, graph_list)
    # flow_controller.control_flow()


    # counter = Counter()
    # avg_flow_num = 250
    #
    # # the weight smaller than the threshold will be shared
    # threshold = 0
    #
    # # build topo from csv files
    # topo_builder = TopoBuilder()
    # topo_builder.gen_topo()
    # graph_list = topo_builder.graph_list
    #
    # # Initialize flow generator with the number of flows
    # flow_generator = FlowGenerator(graph_list, avg_flow_num)
    # flows = flow_generator.generate_flows_for_each_graph()
    #
    # # process flows
    # flow_controller = FlowController(flows, graph_list, threshold)
    # flow_controller.control_flow()
    #
    # #
    # link_usage = counter.get_link_utilization()
    # total_cost = counter.get_total_cost(graph_list)
    #
    # # 打印统计结果
    # print("Total Cost: ", total_cost)
    # print("Link usage:", link_usage)
    #
    # print("Total Flow Num:", counter.total_flows, "threshold: ", threshold,  "blocked rate: ",
    #       counter.get_blocked_rate(), '%')
    # # --------------------------------------------------------------------------------------
    # # 不同阈值
    # # --------------------------------------------------------------------------------------
    #
    # # 创建保存阈值和对应的阻塞率的列表
    # threshold_values = [i for i in range(0, 10)]  # 阈值从0到1，每次增加0.1
    # blocked_rates = []
    # total_flows_accumulated = 0
    # total_blocked_flows = 0
    #
    # # 针对每个阈值生成流量并计算阻塞率
    # for threshold in threshold_values:
    #     for _ in range(5):
    #         # generate flows
    #         counter = Counter()
    #         avg_flow_num = 80
    #
    #         # build topo from csv files
    #         topo_builder = TopoBuilder()
    #         topo_builder.load_graphs()
    #         graph_list = topo_builder.graph_list
    #
    #         # Initialize flow generator with the number of flows
    #         flow_generator = FlowGenerator(graph_list, avg_flow_num)
    #         flows = flow_generator.generate_flows_for_each_graph()
    #
    #         # process flows
    #         flow_controller = FlowController(flows, graph_list, threshold)
    #         flow_controller.control_flow()
    #
    #         print("Total Flow Num:", counter.total_flows, "threshold: ", threshold, "blocked rate: ",
    #               counter.get_blocked_rate(), '%', "blocked_flows", counter.blocked_flows)
    #
    #         total_flows_accumulated += counter.total_flows
    #         total_blocked_flows += counter.blocked_flows
    #
    #         counter.reset_counter()
    #
    #     blocked_rate = total_blocked_flows / total_flows_accumulated
    #     blocked_rate = round(blocked_rate, 1)
    #     blocked_rates.append(blocked_rate)
    #
    # # 绘制图像
    # plt.figure(figsize=(8, 6))
    # plt.plot(threshold_values, blocked_rates, marker='o')
    # plt.xlabel('Threshold')
    # plt.ylabel('Blocked Rate (%)')
    # plt.title('Blocked Rate vs Threshold')
    # plt.grid(True)
    # plt.xticks(threshold_values)
    #
    # # 显示图像
    # plt.show()

    # # --------------------------------------------------------------------------------------
    # # 热图部分
    # # --------------------------------------------------------------------------------------
    #
    # flow_generator = FlowGenerator()
    #
    # flow_generator.generate_flows_for_plotting(20000)
    #
    # satellite_visualizer = SatelliteVisualizer()
    #
    # # 绘制卫星使用热力图
    # # satellite_visualizer.plot_satellite_usage_heatmap()
    #
    # satellite_visualizer.plot_satellite_usage_heatmap()



if __name__ == '__main__':
    main()
