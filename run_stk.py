import os
import platform
import time
import pandas as pd

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


num_orbit_planes = 4
num_sat_per_plane = 8
time_step = 300  # 5min


def run_stk():
    start_time = time.time()

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
    print("Loading scenario...")
    stk_root.LoadScenario('D:/STKScenario/star/star.sc')
    scenario = stk_root.CurrentScenario

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
    #
    # # Set time period
    # scenario.SetTimePeriod("1 Aug 2020 16:00:00", "1 Aug 2020 16:30:00")

    #
    # if not use_stk_engine:
    #     # Graphics calls are not available when running STK Engine in NoGraphics mode
    #     stk_root.Rewind()
    #
    # total_time = time.time() - start_time
    # split_time = time.time()
    # print(
    #     "--- Scenario load: {a:4.3f} sec\t\tTotal time: {b:4.3f} sec ---".format(
    #         a=total_time, b=total_time
    #     )
    # )
    #
    # ############################################################################
    # # Constellations and Facility
    # ############################################################################
    # # Create constellation object
    # constellation = scenario.Children.New(
    #     AgESTKObjectType.eConstellation, "IridiumConstellation"
    # )
    #

    # # iridium
    # stk_root.BeginUpdate()
    # for plane_num, RAAN in enumerate(
    #     range(0, 180, 180 // num_orbit_planes), start=1
    # ):  # RAAN in degrees
    #
    #     for sat_num, trueAnomaly in enumerate(
    #         range(0, 360, 360 // num_sat_per_plane), start=1
    #     ):  # trueAnomaly in degrees
    #
    #         # Insert satellite
    #         satellite = scenario.Children.New(
    #             AgESTKObjectType.eSatellite, f"Sat{plane_num}{sat_num}"
    #         )
    #
    #         # Select Propagator
    #         satellite.SetPropagatorType(AgEVePropagatorType.ePropagatorTwoBody)
    #
    #         # Set initial state
    #         two_body_propagator = satellite.Propagator
    #         keplerian = two_body_propagator.InitialState.Representation.ConvertTo(
    #             AgEOrbitStateType.eOrbitStateClassical.eOrbitStateClassical)
    #         keplerian.SizeShapeType = AgEClassicalSizeShape.eSizeShapeSemimajorAxis
    #         keplerian.Orientation.AscNodeType = AgEOrientationAscNode.eAscNodeRAAN
    #         keplerian.LocationType = AgEClassicalLocation.eLocationTrueAnomaly
    #
    #         # Orbital Six Elements
    #         keplerian.SizeShape.SemiMajorAxis = 8200  # km
    #         keplerian.SizeShape.Eccentricity = 0
    #         keplerian.Orientation.Inclination = 90  # degrees
    #         keplerian.Orientation.ArgOfPerigee = 0  # degrees
    #         keplerian.Orientation.AscNode.Value = RAAN  # degrees
    #         # keplerian.Location.Value = trueAnomaly
    #         keplerian.Location.Value = (
    #                 trueAnomaly + (plane_num - 1) * (180 // num_orbit_planes // num_sat_per_plane)
    #         )  # true anomalies (degrees) for every other orbital plane
    #
    #         # Propagate
    #         satellite.Propagator.InitialState.Representation.Assign(keplerian)
    #         satellite.Propagator.Propagate()
    #
    #         # Add to constellation object
    #         constellation.Objects.AddObject(satellite)
    #
    # stk_root.EndUpdate()
    #
    # # Create faciliy
    # facility = scenario.Children.New(AgESTKObjectType.eFacility, "MyFacility")
    #
    # # Set position
    # facility.Position.AssignGeodetic(28.62, -80.62, 0.03)

    # # Create fac to sat Chain
    # chain = scenario.Children.New(AgESTKObjectType.eChain, "Chain")
    #
    # # Add satellite constellation and facility
    # chain.Objects.AddObject(constellation)
    # chain.Objects.AddObject(facility)

    ############################################################################
    # create access report
    ############################################################################
    # create chain
    print("Creating chain...")
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
    unique_times_list = list(unique_times)
    unique_times_list.sort()

    # write distance and time data in files
    print("Saving data...")
    directory = './data'  # 注意Windows中可能需要使用绝对路径或其他路径格式，例如 'C:/data'
    if not os.path.exists(directory):
        os.makedirs(directory)
    else:
        distance_data = []
        for satellite_pair, distance_list in sat_distance.items():
            for distance in distance_list:
                distance_data.append([satellite_pair, distance])
        distance_df = pd.DataFrame(distance_data, columns=['SatellitePair', 'Distance'])
        time_series = pd.Series(unique_times_list, name='Time Series')
        distance_df.to_csv(f'{directory}/satellite_distances.csv', index=False)
        time_series.to_csv(f'{directory}/time_series.csv', index=False)

        # stk_root.CloseScenario()
        # print("\nClosed scenario successfully.")

    # # Compute chain
    # chain.ComputeAccess()
    #
    # # Find satellite with most access time
    # chainDataProvider = chain.DataProviders.GetDataPrvIntervalFromPath("Object Access")
    # chainResults = chainDataProvider.Exec(scenario.start_time, scenario.stop_time)
    #
    # objectList = []
    # durationList = []
    #
    # # Loop through all satellite access intervals
    # for intervalNum in range(chainResults.Intervals.Count - 1):
    #
    #     # Get interval
    #     interval = chainResults.Intervals[intervalNum]
    #
    #     # Get data for interval
    #     objectName = interval.DataSets.GetDataSetByName("Strand Name").GetValues()[0]
    #     durations = interval.DataSets.GetDataSetByName("Duration").GetValues()
    #
    #     # Add data to list
    #     objectList.append(objectName)
    #     durationList.append(sum(durations))
    #
    # # Find object with longest total duration
    # index = durationList.index(max(durationList))
    # print(
    #     "\n{a:s} has the longest total duration: {b:4.2f} minutes.".format(
    #         a=objectList[index], b=durationList[index]
    #     )
    # )

    # close STK
    # stk_root.CloseScenario()
    # stk.ShutDown()
    # print("\nClosed STK successfully.")


def compute_sat_access(scenario, sat1, sat2):
    # check validation
    if not sat1 or not sat2:
        print("一个或两个卫星对象无效。")

    # compute access
    access = sat1.GetAccessToObject(sat2)
    if not access:
        print("访问对象无效。")
    else:
        access.ComputeAccess()
        # get dataprovider
        rpt_elms = ["Time", "Range"]
        access_DP = access.DataProviders.GetDataPrvTimeVarFromPath("AER Data/Default")
        # access_DP = (access.DataProviders.Item('AER Data').Group.Item('Default').
        #             Exec(scenario.start_time, scenario.stop_time, rpt_elms))
        if not access_DP:
            print("访问数据提供者对象无效。")
        else:
            # get distances
            access_result = access_DP.ExecElements(scenario.StartTime, scenario.StopTime, time_step, rpt_elms)
            sce_time = access_result.DataSets.GetDataSetByName('Time').GetValues()
            sat_range = access_result.DataSets.GetDataSetByName('Range').GetValues()
            return sce_time, sat_range
            # Data = pd.DataFrame(columns=('Time (UTC)', 'Range (km)'))
            # for j in range(0, len(sce_time)):
            #     t = sce_time[j]
            #     ran = sat_range[j]
            #     Data = Data.append(pd.DataFrame(
            #         {'Time (UTC)': [t],
            #          'Range (km)': [ran]}),
            #         ignore_index=True)
            #     print(Data.head())

            # sat_range = access_DP.DataSets.GetDataSetByName('range').GetValues
            # print(sat_range)


# 运行主程序
if __name__ == "__main__":
    run_stk()

