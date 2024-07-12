# -*- coding: utf-8 -*-
# @Time    : 2024/4/13 16:51
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : run_stk.py

import os
import platform
import time
import pandas as pd
from datetime import datetime
from sim_config import *
import re

from agi.stk12.stkobjects import (
    AgEClassicalLocation,
    AgEClassicalSizeShape,
    AgECvBounds,
    AgECvResolution,
    AgEFmCompute,
    AgEFmDefinitionType,
    AgEOrientationAscNode,
    AgESTKObjectType,
    AgEVePropagatorType,
)
from agi.stk12.stkdesktop import STKDesktop
from agi.stk12.stkutil import AgEOrbitStateType


def run_stk():
    start_time = time.time()
    split_time = time.time()
    """
    SET TO TRUE TO USE ENGINE, FALSE TO USE GUI
    """
    if platform.system() == "Linux":
        # Only STK Engine is available on Linux
        use_stk_engine = True
    else:
        # Change to true to run engine on Windows
        use_stk_engine = False

    # use existing scenario
    stk = STKDesktop.AttachToApplication()
    stk_root = stk.Root
    # Set date format
    stk_root.UnitPreferences.SetCurrentUnit("DateFormat", "UTCG")
    # load scenario
    print("Loading scenario...", end='')
    stk_root.LoadScenario('D:/STKScenario/star_blank/star.sc')
    scenario = stk_root.CurrentScenario

    # Set time period
    scenario.SetTimePeriod("1 Aug 2020 16:00:00", "1 Aug 2020 16:30:00")

    if not use_stk_engine:
        # Graphics calls are not available when running STK Engine in NoGraphics mode
        stk_root.Rewind()

    # time analyse
    total_time = time.time() - start_time
    section_time = time.time() - split_time
    split_time = time.time()
    print(
        "Scenario load: {a:4.3f} sec\t\tTotal time: {b:4.3f} sec".format(
            a=section_time, b=total_time
        )
    )
    # ###########################################################################
    # # Scenario Setup
    # ###########################################################################
    # # launch stk
    # if use_stk_engine:
    #     from agi.stk12.stkengine import STKEngine
    #
    #     # Launch STK Engine with NoGraphics mode
    #     print("Launching STK Engine...")
    #     stk = STKEngine.StartApplication(noGraphics=True)
    #
    #     # Create root object
    #     stk_root = stk.NewObjectRoot()
    #
    # else:
    #     from agi.stk12.stkdesktop import STKDesktop
    #
    #     # Launch GUI
    #     print("Launching STK...")
    #     stk = STKDesktop.StartApplication(visible=True, userControl=True)
    #
    #     # Get root object
    #     stk_root = stk.Root
    #
    #
    #
    # # Create new scenario
    # print("Creating scenario...")
    # stk_root.NewScenario("Star")
    # scenario = stk_root.CurrentScenario

    ############################################################################
    # Constellations and Facility
    ############################################################################
    # Create constellation object
    constellation = scenario.Children.New(
        AgESTKObjectType.eConstellation, "IridiumConstellation"
    )

    # iridium
    stk_root.BeginUpdate()
    for plane_num, RAAN in enumerate(
        range(0, 180, 180 // num_orbit_planes), start=1
    ):  # RAAN in degrees

        for sat_num, trueAnomaly in enumerate(
            range(0, 360, 360 // num_sat_per_plane), start=1
        ):  # trueAnomaly in degrees

            # Insert satellite
            satellite = scenario.Children.New(
                AgESTKObjectType.eSatellite, f"Sat{plane_num}{sat_num}"
            )

            # Select Propagator
            satellite.SetPropagatorType(AgEVePropagatorType.ePropagatorTwoBody)

            # Set initial state
            two_body_propagator = satellite.Propagator
            keplerian = two_body_propagator.InitialState.Representation.ConvertTo(
                AgEOrbitStateType.eOrbitStateClassical.eOrbitStateClassical)
            keplerian.SizeShapeType = AgEClassicalSizeShape.eSizeShapeSemimajorAxis
            keplerian.Orientation.AscNodeType = AgEOrientationAscNode.eAscNodeRAAN
            keplerian.LocationType = AgEClassicalLocation.eLocationTrueAnomaly

            # Orbital Six Elements
            keplerian.SizeShape.SemiMajorAxis = 8200  # km
            keplerian.SizeShape.Eccentricity = 0
            keplerian.Orientation.Inclination = 90  # degrees
            keplerian.Orientation.ArgOfPerigee = 0  # degrees
            keplerian.Orientation.AscNode.Value = RAAN  # degrees
            # keplerian.Location.Value = trueAnomaly
            keplerian.Location.Value = (
                    trueAnomaly + (plane_num - 1) * (180 // num_orbit_planes // num_sat_per_plane)
            )  # true anomalies (degrees) for every other orbital plane

            # Propagate
            satellite.Propagator.InitialState.Representation.Assign(keplerian)
            satellite.Propagator.Propagate()

            # Add to constellation object
            constellation.Objects.AddObject(satellite)

    stk_root.EndUpdate()  # Apply changes




    ############################################################################
    # create access & report
    ############################################################################
    print("Creating access&report...", end='')

    # create inter-sat access
    sat_distance = {}
    unique_times = set()
    all_satellites = scenario.Children.GetElements(AgESTKObjectType.eSatellite)
    for plane_num in range(1, num_orbit_planes + 1):
        for sat_num in range(1, num_sat_per_plane + 1):
            # satellite name init
            cur_sat_name = f"Sat{plane_num}{sat_num}"
            if plane_num < num_orbit_planes:
                intra_sat_name = f"Sat{plane_num + 1}{sat_num}"
                intra_sat = next(sat for sat in all_satellites if sat.InstanceName == intra_sat_name)
            else:
                intra_sat_name = 0
                intra_sat = 0

            # circle connect
            if sat_num == num_sat_per_plane:
                inter_sat_name = f"Sat{plane_num}1"
            else:
                inter_sat_name = f"Sat{plane_num}{sat_num + 1}"
            cur_sat = next(sat for sat in all_satellites if sat.InstanceName == cur_sat_name)
            inter_sat = next(sat for sat in all_satellites if sat.InstanceName == inter_sat_name)
            # print(f"current:{cur_sat_name}, inter_sat_name:{inter_sat_name}, intra_sat_name:{intra_sat_name}")

            # create access
            if inter_sat:
                # inter sat distance
                sce_time, sat_distance[f"{cur_sat_name} to {inter_sat_name}"] = compute_sat_access(
                    scenario, cur_sat, inter_sat)
                unique_times.update(sce_time)
                # print(f"{cur_sat_name} to {inter_sat_name} distance:")
                # for temp_time, temp_range in zip(temp_times, temp_ranges):
                #     print(f"{temp_time}\t{temp_range}")
            if intra_sat:
                # intra sat distance
                sce_time, sat_distance[f"{cur_sat_name} to {intra_sat_name}"] = compute_sat_access(
                    scenario, cur_sat, intra_sat)
                unique_times.update(sce_time)
                # print(f"{cur_sat_name} to {intra_sat_name} distance:")
                # for temp_time, temp_range in zip(temp_times, temp_ranges):
                #     print(f"{temp_time}\t{temp_range}")

        # # Iterate print
        # for list_key, list_value in sat_distance.items():
        #     print(f"distance from {list_key} is: {list_value}")

    # sort the time list
    time_list = list(unique_times)
    time_list.sort()

    # time analyse
    total_time = time.time() - start_time
    section_time = time.time() - split_time
    split_time = time.time()
    print(
        "access created: {a:4.3f} sec\t\tTotal time: {b:4.3f} sec".format(
            a=section_time, b=total_time
        )
    )

    ############################################################################
    # create chain & report
    ############################################################################
    print("Creating chain&report...", end='')

    # Create faciliy
    Myfacility = scenario.Children.New(AgESTKObjectType.eFacility, "MyFacility")

    # Set position
    Myfacility.Position.AssignGeodetic(28.62, -80.62, 0.03)

    # Compute chain
    compute_fac_access(scenario, time_list, Myfacility, constellation)

    # time analyse
    total_time = time.time() - start_time
    section_time = time.time() - split_time
    split_time = time.time()
    print(
        "chain created: {a:4.3f} sec\t\tTotal time: {b:4.3f} sec".format(
            a=section_time, b=total_time
        )
    )

    ############################################################################
    # saving data
    ############################################################################
    print("Saving data...", end='')
    directory = './data'
    if not os.path.exists(directory):
        os.makedirs(directory)
    else:
        distance_data = []
        for satellite_pair, distance_list in sat_distance.items():
            for distance in distance_list:
                distance_data.append([satellite_pair, distance])
        distance_df = pd.DataFrame(distance_data, columns=['SatellitePair', 'Distance'])
        # chain_df = pd.DataFrame(chain_data)
        time_series = pd.Series(time_list, name='Time Series')

        # use pandas to save
        distance_df.to_csv(f'{directory}/satellite_distances.csv', index=False)
        # chain_df.to_csv(f'{directory}/chain.csv', index=False)
        time_series.to_csv(f'{directory}/time_series.csv', index=False)

        # time analyse
        total_time = time.time() - start_time
        section_time = time.time() - split_time
        split_time = time.time()
        print(
            "data saved: {a:4.3f} sec\t\tTotal time: {b:4.3f} sec".format(
                a=section_time, b=total_time
            )
        )
        # stk_root.CloseScenario()
        # print("\nClosed scenario successfully.")

    # close STK
    # stk_root.CloseScenario()
    # stk.ShutDown()
    # print("\nClosed STK successfully.")


def compute_sat_access(scenario, sat1, sat2):
    # check validation
    if not sat1 or not sat2:
        print("satellite is not valid")

    # compute access
    access = sat1.GetAccessToObject(sat2)
    if not access:
        print("access object not valid")
    else:
        access.ComputeAccess()
        # get dataprovider
        rpt_elms = ["Time", "Range"]
        access_DP = access.DataProviders.GetDataPrvTimeVarFromPath("AER Data/Default")
        # access_DP = (access.DataProviders.Item('AER Data').Group.Item('Default').
        #             Exec(scenario.start_time, scenario.stop_time, rpt_elms))
        if not access_DP:
            print("data provider not valid")
        else:
            # get distances
            access_result = access_DP.ExecElements(scenario.StartTime, scenario.StopTime, time_step, rpt_elms)
            time_origin = access_result.DataSets.GetDataSetByName('Time').GetValues()
            sat_range = access_result.DataSets.GetDataSetByName('Range').GetValues()

            # Convert the truncated time string to a datetime object
            sce_times = truncate_times(time_origin)
            distance_between_sats = round_distances(sat_range)
            return sce_times, distance_between_sats


# calculate distance between sat and fac
def compute_fac_access(scenario, time_list, facility, constellation):
    # Create fac to sat Chain
    chain = scenario.Children.New(AgESTKObjectType.eChain, "Chain")

    # Add satellite constellation and facility
    chain.Objects.AddObject(constellation)
    chain.Objects.AddObject(facility)
    chain.ComputeAccess()

    # get data provider range data is TimeVar
    rpt_elms = ["Time", "Strand Name", "Range"]
    # chainDataProvider = chain.DataProviders.GetDataPrvIntervalFromPath("Range Data")
    chainDataProvider = chain.DataProviders.GetDataPrvTimeVarFromPath("Range Data")
    # chainResults = chainDataProvider.Exec(scenario.StartTime, scenario.StopTime, 300, rpt_elms)
    chainResults = chainDataProvider.ExecElements(scenario.StartTime, scenario.StopTime, time_step, rpt_elms)

    # Loop through all satellite access intervals
    for intervalNum in range(chainResults.Intervals.Count):
        # Get interval
        interval = chainResults.Intervals[intervalNum]

        # Get data for interval
        chain_times = interval.DataSets.GetDataSetByName("Time").GetValues()
        strand_names = interval.DataSets.GetDataSetByName("Strand Name").GetValues()
        sat_fac_distances = interval.DataSets.GetDataSetByName("Range").GetValues()

        # Process each data point
        chain_times = truncate_times(chain_times)
        chain_time_list = approximate_time(chain_times, time_list)
        sat_fac_distances = round_distances(sat_fac_distances)
        sat_name, fac_name = extract_pattern_from_string(strand_names[0], pattern=r"\/(\w+)\s+To\s+.*\/(\w+)")
        print("start to print chain data...", end='')

        directory = f'./data/fac_sat_chain'
        if not os.path.exists(directory):
            os.makedirs(directory)
        else:
            # make sure have the same
            if len(chain_time_list) != len(sat_fac_distances):
                raise ValueError("Time list and distances list must be of the same length")

            # 创建包含多个列的 DataFrame
            processed_data = list(zip(chain_time_list, sat_fac_distances))
            distance_df = pd.DataFrame(processed_data, columns=['Time', 'Distance'])
            distance_df.to_csv(f'{directory}/{sat_name} To {fac_name}.csv', index=False)
        print(f"Data saved to {directory}/{sat_name} To {fac_name}.csv")
    # return


# Function to approximate each time point in time_origin to the nearest time point in time_list, rounding down
def approximate_time(time_origin, time_list):
    approximated_times = []
    for time_temp in time_origin:
        approx_time = None
        for tl_time in time_list:
            if tl_time > time_temp:
                break
            approx_time = tl_time
        if approx_time is not None:
            approximated_times.append(approx_time)
    return approximated_times


# Truncate the given time string to remove microseconds or smaller units.
def truncate_times(time_list, format_str="%d %b %Y %H:%M:%S"):
    dt_times = []
    for time_str in time_list:
        # Strip off any microseconds or smaller units by truncating the string at the last '.'
        if '.' in time_str:
            time_str = time_str[:time_str.rfind('.')]
        # Convert the truncated time string to a datetime object
        dt_time = datetime.strptime(time_str, format_str)
        # Add the datetime object to the list
        dt_times.append(dt_time)
    return dt_times


def extract_pattern_from_string(input_string, pattern, default='Unknown'):
    # Extracts a specific pattern from the given string using regular expressions.
    match = re.search(pattern, input_string)
    if match:
        return match.group(1), match.group(2)
    else:
        return default, default


def round_distances(distances):
    # Rounding off the distance
    return [round(distance) for distance in distances]


# 运行主程序
if __name__ == "__main__":
    run_stk()
