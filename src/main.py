# -*- coding: utf-8 -*-
# @Time    : 2024/7/14 15:41
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : main.py

import os
import sys

import counter
import stk
from pathlib import Path
from stk.stk_manager import STKManager
from network.topo_builder import TopoBuilder
from network.flow_controller import FlowController
from utils.counter import Counter


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
    topo_builder = TopoBuilder()
    topo_builder.gen_topo()

    # generate traffic
    flow_controller = FlowController()
    flow_controller.control_fow()

    print("blocked services: ", flow_controller.counter.blocked_services)

    # print("total services: ", flow_controller.counter.total_services)
    # print("blocked rate: ", flow_controller.counter.get_blocked_rate())
    # print("failure count: ", flow_controller.failure_count)


if __name__ == '__main__':
    main()
