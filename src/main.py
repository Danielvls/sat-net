# -*- coding: utf-8 -*-
# @Time    : 2024/7/14 15:41
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : main.py

import os
import sys


import stk
from pathlib import Path
from stk.stk_manager import STKManager
from network.topo_builder import TopoBuilder
from network.flow_controller import FlowController
from utils.counter import Counter
from utils.utils import timeit_decorator


@timeit_decorator
def main():
    # manager = STKManager()
    # manager.attach_to_application()
    # manager.load_scenario('D:/STKScenario/star_blank/star.sc',
    #                       "1 Aug 2020 16:00:00", "1 Aug 2020 16:30:00")
    # manager.create_constellation()
    # manager.create_facilities()
    # manager.create_access()
    # manager.save_data()

    # build topo from csv files
    # topo_builder = TopoBuilder()
    # topo_builder.gen_topo()

    # for i in [x * 0.02 for x in range(10)]:
    #     thershold = i

    # generate flows
    counter = Counter()
    thershold = 0.2
    num_flows = 20
    flow_controller = FlowController(thershold, num_flows, counter)
    flow_controller.control_fow()
    print("thershold: ", thershold,  "blocked rate: ", flow_controller.counter.get_blocked_rate(), '%')

    # print("total services: ", flow_controller.counter.total_services)
    # print("blocked rate: ", flow_controller.counter.get_blocked_rate())
    # print("failure count: ", flow_controller.failure_count)


if __name__ == '__main__':
    main()
