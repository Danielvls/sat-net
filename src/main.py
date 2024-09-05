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
from utils.counter import Counter
from utils.utils import timeit_decorator
import pandas as pd
import numpy as np
from timeit import default_timer as timer
import matplotlib.pyplot as plt
from proplot import rc
import seaborn as sns


@timeit_decorator
def main():
    # # start profiling
    # manager = STKManager()
    # manager.launch_stk()
    # manager.attach_to_application()
    # # manager.load_scenario('D:/STKScenario/star_blank/star.sc',
    # #                       "1 Aug 2020 16:00:00", "2 Aug 2020 16:00:00")
    # manager.create_scenario("IridiumConstellation", "1 Aug 2020 16:00:00", "1 Aug 2020 17:00:00")
    # manager.create_constellation()
    # manager.create_facilities()
    # manager.create_access()
    # manager.save_data()

    # Define parameters
    avg_flow_nums = list(range(70, 81, 10))
    thresholds = [i * 1 for i in range(2)]  # Generate values from 0 to 3 with a step of 0.5

    # Initialize a CSV file to store the summary data
    csv_filename = 'summary_blocked_rate_data.csv'
    columns = ["Avg Flow Num", "Threshold", "Mean Blocked Rate (%)", "Std Dev Blocked Rate (%)", "Mean Total Flows"]
    pd.DataFrame(columns=columns).to_csv(csv_filename, index=False)

    results = []

    for avg_flow_num in avg_flow_nums:
        for threshold in thresholds:
            total_blocked_flows = 0
            total_flows_accumulated = 0
            blocked_rates = []  # Store results of 5 runs

            for _ in range(5):
                start_time = timer()

                counter = Counter()

                topo_builder = TopoBuilder()
                topo_builder.load_graphs()

                graph_list = topo_builder.graph_list

                flow_generator = FlowGenerator(graph_list, avg_flow_num)
                flows = flow_generator.generate_flows()

                flow_controller = FlowController(threshold, counter, flows, graph_list)
                flow_controller.control_flow()

                blocked_rate = flow_controller.counter.get_blocked_rate()
                blocked_rates.append(blocked_rate)

                total_flows_accumulated += counter.total_flows
                total_blocked_flows += counter.blocked_flows

                end_time = timer()
                execution_time = end_time - start_time

                print(
                    f"Total Flow Num: {counter.total_flows}, Threshold: {threshold}, Blocked Rate: {blocked_rate}%, "
                    f"Execution Time: {execution_time} seconds")

            # Calculate mean and std deviation for blocked rate
            mean_blocked_rate = np.mean(blocked_rates)
            std_blocked_rate = np.std(blocked_rates)
            mean_total_flows = total_flows_accumulated / 5  # Average total flows over the 5 runs

            # Store results for plotting
            results.append({
                "Avg Flow Num": avg_flow_num,
                "Threshold": threshold,
                "Mean Blocked Rate (%)": mean_blocked_rate,
                "Std Dev Blocked Rate (%)": std_blocked_rate,
                "Mean Total Flows": mean_total_flows
            })

            # Record summary data into the CSV file
            summary_data = pd.DataFrame([{
                "Avg Flow Num": avg_flow_num,
                "Threshold": threshold,
                "Mean Blocked Rate (%)": mean_blocked_rate,
                "Std Dev Blocked Rate (%)": std_blocked_rate,
                "Mean Total Flows": mean_total_flows
            }])
            summary_data.to_csv(csv_filename, mode='a', header=False, index=False)

    # Plot the results
    df_results = pd.DataFrame(results)

    # Define parameters for plotting
    markers = ["o", "s", "D", "^"]
    colors = ["#2FBE8F", "#459DFF", "#FF5B9B", "#FFCC37"]

    # Plotting
    fig, ax = plt.subplots(figsize=(8, 6), dpi=100)

    for i, avg_flow_num in enumerate(avg_flow_nums):
        subset = df_results[df_results["Avg Flow Num"] == avg_flow_num]
        if subset.empty:
            continue

        x = subset["Threshold"].values
        y = subset["Mean Blocked Rate (%)"].values
        yerr = subset["Std Dev Blocked Rate (%)"].values

        ax.errorbar(x, y, yerr=yerr, fmt=markers[i], markersize=8, capsize=5, color=colors[i],
                    label=f'Avg Flow Num {avg_flow_num}', linestyle='-', linewidth=1)

    ax.set_ylim(-8, 30)
    ax.set_xlim(-2, 40)
    ax.set_xlabel("Threshold")
    ax.set_ylabel("Mean Blocked Rate (%)")
    ax.set_title("Blocked Rate vs. Threshold")
    ax.legend()
    plt.tight_layout()
    plt.savefig('blocked_rate_plot.pdf', bbox_inches='tight')
    plt.savefig('blocked_rate_plot.png', bbox_inches='tight', dpi=300)
    plt.show()

    # # generate flows
    # counter = Counter()
    # avg_flow_num = 100
    #
    # # the weight smaller than the threshold will be shared
    # threshold = 10
    #
    # # build topo from csv files
    # topo_builder = TopoBuilder()
    # topo_builder.gen_topo()
    #
    # graph_list = topo_builder.graph_list
    # # Initialize flow generator with the number of flows
    # flow_generator = FlowGenerator(graph_list, avg_flow_num)
    # flows = flow_generator.generate_flows()
    #
    # # process flows
    # flow_controller = FlowController(threshold, counter, flows, graph_list)
    # flow_controller.control_flow()
    #
    # print("Total Flow Num:", counter.total_flows, "threshold: ", threshold,  "blocked rate: ",
    #       flow_controller.counter.get_blocked_rate(), '%')


if __name__ == '__main__':
    main()
