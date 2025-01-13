# -*- coding: utf-8 -*-
# @Time    : 2024/7/14 15:41
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : main.py


import pstats
import io
from stk.stk_manager import STKManager
from network.topo_builder import TopoBuilder
from network.flow_generator import FlowGenerator
from network.flow_controller import FlowController
# from plot.satellite_visualizer import SatelliteVisualizer
from src.utils import Counter
from utils.utils import timeit_decorator
import pandas as pd
import numpy as np
from pathlib import Path
from timeit import default_timer as timer
import matplotlib.pyplot as plt


@timeit_decorator
def main():
    # # --------------------------------------------------------------------------------------
    # # stk 部分
    # # --------------------------------------------------------------------------------------
    # Initialize STK Manager
    manager = STKManager()
    manager.launch_stk()
    manager.attach_to_application()
    # manager.load_scenario('D:/STKScenario/star_blank/star.sc',
    #                       "1 Aug 2020 16:00:00", "2 Aug 2020 16:00:00")
    manager.create_scenario("1 Aug 2020 16:00:00", "1 Aug 2020 16:30:00")
    manager.create_constellation("DeltaConstellation")
    manager.create_facilities()
    manager.create_access()
    # manager.get_sat_lla()
    # manager.save_data()

    # # --------------------------------------------------------------------------------------
    # # 结果图部分
    # # --------------------------------------------------------------------------------------

    # # Define parameters for the simulation
    # avg_flow_nums = list(range(150, 251, 10))  # Avg Flow Num from 150 to 250 with step size of 10
    # threshold = 2
    #
    # # Initialize CSV files to store the summary data
    # csv_cost_filename = 'result/summary_total_cost_2.csv'
    # csv_usage_filename = 'result/summary_link_usage_2.csv'
    # csv_blocked_rate_filename = 'result/summary_blocked_rate_2.csv'
    #
    # cost_columns = ["Avg Flow Num", "Threshold", "Mean Total Cost", "Std Dev Total Cost"]
    # usage_columns = ["Avg Flow Num", "Threshold", "Mean Link Usage", "Std Dev Link Usage"]
    # blocked_rate_columns = ["Avg Flow Num", "Threshold", "Mean Blocked Rate (%)", "Std Dev Blocked Rate (%)"]
    #
    # pd.DataFrame(columns=cost_columns).to_csv(csv_cost_filename, index=False)
    # pd.DataFrame(columns=usage_columns).to_csv(csv_usage_filename, index=False)
    # pd.DataFrame(columns=blocked_rate_columns).to_csv(csv_blocked_rate_filename, index=False)
    #
    # results = []
    # counter = Counter()
    #
    # for avg_flow_num in avg_flow_nums:
    #     print(f"Avg Flow Num: {avg_flow_num}")
    #
    #     total_costs = []
    #     link_usages = []
    #     blocked_rates = []
    #
    #     for _ in range(5):  # Run 5 times to calculate average
    #         start_time = timer()
    #
    #         # Build topology from csv files
    #         topo_builder = TopoBuilder()
    #         topo_builder.load_graphs()
    #         graph_list = topo_builder.graph_list
    #
    #         # Initialize flow generator with the number of flows
    #         flow_generator = FlowGenerator(graph_list, avg_flow_num)
    #         flows = flow_generator.generate_flows_for_each_graph()
    #
    #         # Process flows
    #         flow_controller = FlowController(flows, graph_list, threshold)
    #         flow_controller.control_flow()
    #
    #         # Get link usage, total cost, and blocked rate
    #         link_usage = counter.get_link_utilization()
    #         total_cost = counter.get_total_cost(graph_list)
    #         blocked_rate = flow_controller.counter.get_blocked_rate()
    #         blocked_rate = round(blocked_rate, 1)
    #
    #         total_costs.append(total_cost)
    #         link_usages.append(link_usage)
    #         blocked_rates.append(blocked_rate)
    #
    #         end_time = timer()
    #         execution_time = end_time - start_time
    #         execution_time = round(execution_time, 1)
    #
    #         # Print the statistics for each run
    #         print(
    #             f"Run {_ + 1}: Total Flow Num: {counter.total_flows}, Threshold: {threshold}, Blocked Rate: {blocked_rate}%, "
    #             f"Total Cost: {total_cost}, Link Usage: {link_usage}, Execution Time: {execution_time} seconds")
    #
    #         # Reset counter for next iteration
    #         counter.reset_counter()
    #
    #     # Calculate mean and standard deviation for metrics
    #     mean_blocked_rate = np.mean(blocked_rates)
    #     std_blocked_rate = np.std(blocked_rates)
    #     mean_total_cost = np.mean(total_costs)
    #     std_total_cost = np.std(total_costs)
    #     mean_link_usage = np.mean(link_usages)
    #     std_link_usage = np.std(link_usages)
    #
    #     # Store results for plotting
    #     results.append({
    #         "Avg Flow Num": avg_flow_num,
    #         "Threshold": threshold,
    #         "Mean Total Cost": mean_total_cost,
    #         "Std Dev Total Cost": std_total_cost,
    #         "Mean Link Usage": mean_link_usage,
    #         "Std Dev Link Usage": std_link_usage,
    #         "Mean Blocked Rate (%)": mean_blocked_rate,
    #         "Std Dev Blocked Rate (%)": std_blocked_rate
    #     })
    #
    #     # Record summary data into the CSV files
    #     cost_data = pd.DataFrame([{
    #         "Avg Flow Num": avg_flow_num,
    #         "Threshold": threshold,
    #         "Mean Total Cost": mean_total_cost,
    #         "Std Dev Total Cost": std_total_cost
    #     }])
    #     cost_data.to_csv(csv_cost_filename, mode='a', header=False, index=False)
    #
    #     usage_data = pd.DataFrame([{
    #         "Avg Flow Num": avg_flow_num,
    #         "Threshold": threshold,
    #         "Mean Link Usage": mean_link_usage,
    #         "Std Dev Link Usage": std_link_usage
    #     }])
    #     usage_data.to_csv(csv_usage_filename, mode='a', header=False, index=False)
    #
    #     blocked_rate_data = pd.DataFrame([{
    #         "Avg Flow Num": avg_flow_num,
    #         "Threshold": threshold,
    #         "Mean Blocked Rate (%)": mean_blocked_rate,
    #         "Std Dev Blocked Rate (%)": std_blocked_rate
    #     }])
    #     blocked_rate_data.to_csv(csv_blocked_rate_filename, mode='a', header=False, index=False)
    #
    # # Plotting the results with error bars
    # avg_flow_nums = [result["Avg Flow Num"] for result in results]
    #
    # # Plot Total Cost with error bars
    # mean_total_costs = [result["Mean Total Cost"] for result in results]
    # std_total_costs = [result["Std Dev Total Cost"] for result in results]
    # plt.errorbar(avg_flow_nums, mean_total_costs, yerr=std_total_costs, fmt='o-', ecolor='r', capsize=5,
    #              label='Total Cost')
    # plt.xlabel('Average Flow Number')
    # plt.ylabel('Mean Total Cost')
    # plt.title('Total Cost vs Average Flow Number with Error Bars')
    # plt.legend()
    # plt.grid(True)
    # plt.savefig('result/total_cost_vs_avg_flow_num_2.png')
    # plt.show()
    #
    # # Plot Link Usage with error bars
    # mean_link_usages = [result["Mean Link Usage"] for result in results]
    # std_link_usages = [result["Std Dev Link Usage"] for result in results]
    # plt.errorbar(avg_flow_nums, mean_link_usages, yerr=std_link_usages, fmt='o-', ecolor='r', capsize=5,
    #              label='Link Usage')
    # plt.xlabel('Average Flow Number')
    # plt.ylabel('Mean Link Usage')
    # plt.title('Link Usage vs Average Flow Number with Error Bars')
    # plt.legend()
    # plt.grid(True)
    # plt.savefig('result/link_usage_vs_avg_flow_num_2.png')
    # plt.show()
    #
    # # Plot Blocked Rate with error bars
    # mean_blocked_rates = [result["Mean Blocked Rate (%)"] for result in results]
    # std_blocked_rates = [result["Std Dev Blocked Rate (%)"] for result in results]
    # plt.errorbar(avg_flow_nums, mean_blocked_rates, yerr=std_blocked_rates, fmt='o-', ecolor='r', capsize=5,
    #              label='Blocked Rate (%)')
    # plt.xlabel('Average Flow Number')
    # plt.ylabel('Mean Blocked Rate (%)')
    # plt.title('Blocked Rate vs Average Flow Number with Error Bars')
    # plt.legend()
    # plt.grid(True)
    # plt.savefig('result/blocked_rate_vs_avg_flow_num_2.png')
    # plt.show()


    # --------------------------------------------------------------------------------------
    # 调试部分
    # --------------------------------------------------------------------------------------
    # counter = Counter()
    # avg_flow_num = 250
    #
    # # the weight smaller than the threshold will be shared
    # threshold = 0
    #
    # # build topo from csv files
    topo_builder = TopoBuilder()
    topo_builder.gen_topo()
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
