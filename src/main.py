# -*- coding: utf-8 -*-
# @Time    : 2024/7/14 15:41
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : main.py

import cProfile
import pstats
import io
from stk.stk_manager import STKManager
from network.topo_builder import TopoBuilder
from network.flow_controller import FlowController
from utils.counter import Counter
from utils.utils import timeit_decorator
import pandas as pd
from timeit import default_timer as timer


@timeit_decorator
def main():
    # # start profiling
    # profiler = cProfile.Profile()
    # profiler.enable()

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
    #
    # # build topo from csv files
    # topo_builder = TopoBuilder()
    # topo_builder.gen_topo()

    # # Define parameters for testing
    # avg_flow_nums = list(range(10, 101, 10))
    # thersholds = [i * 0.5 for i in range(7)]  # Generates values from 0 to 3 in steps of 0.5
    #
    # # Initialize an empty DataFrame
    # results_df = pd.DataFrame(index=thersholds, columns=avg_flow_nums)
    # results_df.to_csv('blocked_rate_matrix.csv')  # Write the initial structure with row and column headers to the CSV
    #
    # for avg_flow_num in avg_flow_nums:
    #     for thershold in thersholds:
    #         start_time = timer()
    #
    #         # Assuming the existence of a counter and flow_controller implementation
    #         counter = Counter()
    #         flow_controller = FlowController(thershold, counter, avg_flow_num)
    #         flow_controller.control_fow()
    #
    #         blocked_rate = flow_controller.counter.get_blocked_rate()
    #         end_time = timer()
    #         execution_time = end_time - start_time
    #
    #         # Update the specific cell in the DataFrame
    #         results_df.at[thershold, avg_flow_num] = blocked_rate
    #
    #         # Overwrite the entire DataFrame to the file with the updated data
    #         results_df.to_csv('blocked_rate_matrix.csv')
    #
    #         print("Total Flow Num:", counter.total_flows, "Thershold:", thershold, "Blocked Rate:", blocked_rate, '%',
    #               "Execution Time:", execution_time, "seconds")
    #
    # print("All data has been updated in 'blocked_rate_matrix.csv'.")

    # generate flows
    counter = Counter()
    avg_flow_num = 5

    # the weight smaller than the thershold will be shared
    thershold = 0
    flow_controller = FlowController(thershold, counter, avg_flow_num)
    flow_controller.control_fow()
    print("Total Flow Num:", counter.total_flows, "thershold: ", thershold,  "blocked rate: ",
          flow_controller.counter.get_blocked_rate(), '%')

    # # end profiling
    # profiler.disable()
    # s = io.StringIO()
    # sortby = 'cumulative'  # 可以选择不同的排序方式，如'cumulative', 'time'
    # ps = pstats.Stats(profiler, stream=s).sort_stats(sortby)
    # ps.print_stats()
    # print(s.getvalue())


if __name__ == '__main__':
    main()
