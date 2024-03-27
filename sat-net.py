import os
import platform
import time

from agi.stk12.stkobjects import (
    AgEClassicalLocation,
    AgEClassicalSizeShape,
    AgECvBounds,
    AgECvResolution,
    AgEFmCompute,
    AgEFmDefinitionType,
    AgEOrientationAscNode,
    AgESTKObjectType,    AgEVePropagatorType,
)
from agi.stk12.stkdesktop import STKDesktop
from agi.stk12.stkutil import AgEOrbitStateType

numOrbitPlanes = 4
numSatsPerPlane = 8

# 主程序入口
def main():
    startTime = time.time()

    """
    SET TO TRUE TO USE ENGINE, FALSE TO USE GUI
    """
    if platform.system() == "Linux":
        # Only STK Engine is available on Linux
        useStkEngine = True
    else:
        # Change to true to run engine on Windows
        useStkEngine = False

    ############################################################################
    # Scenario Setup
    ############################################################################
    # # launch stk
    # if useStkEngine:
    #     from agi.stk12.stkengine import STKEngine
    #
    #     # Launch STK Engine with NoGraphics mode
    #     print("Launching STK Engine...")
    #     stk = STKEngine.StartApplication(noGraphics=True)
    #
    #     # Create root object
    #     stkRoot = stk.NewObjectRoot()
    #
    # else:
    #     from agi.stk12.stkdesktop import STKDesktop
    #
    #     # Launch GUI
    #     print("Launching STK...")
    #     stk = STKDesktop.StartApplication(visible=True, userControl=True)
    #
    #     # Get root object
    #     stkRoot = stk.Root

    stk = STKDesktop.AttachToApplication()
    stkRoot = stk.Root
    # Set date format
    stkRoot.UnitPreferences.SetCurrentUnit("DateFormat", "UTCG")

    # Create new scenario
    # print("Creating scenario...")
    # stkRoot.NewScenario("PythonEngineExample")

    # load scenario
    print("Loading scenario...")
    stkRoot.LoadScenario('D:/STKScenario/star/star.sc')

    scenario = stkRoot.CurrentScenario
    # Set time period
    scenario.SetTimePeriod("1 Aug 2020 16:00:00", "2 Aug 2020 16:00:00")
    if not useStkEngine:
        # Graphics calls are not available when running STK Engine in NoGraphics mode
        stkRoot.Rewind()

    totalTime = time.time() - startTime
    splitTime = time.time()
    print(
        "--- Scenario load: {a:4.3f} sec\t\tTotal time: {b:4.3f} sec ---".format(
            a=totalTime, b=totalTime
        )
    )

    # ############################################################################
    # # Constellations and Facility
    # ############################################################################
    #
    # # Create constellation object
    # constellation = scenario.Children.New(
    #     AgESTKObjectType.eConstellation, "SatConstellation"
    # )
    #
    # # iridium
    # stkRoot.BeginUpdate()
    # for orbitPlaneNum, RAAN in enumerate(
    #     range(0, 180, 180 // numOrbitPlanes), start=1
    # ):  # RAAN in degrees
    #
    #     for satNum, trueAnomaly in enumerate(
    #         range(0, 360, 360 // numSatsPerPlane), start=1
    #     ):  # trueAnomaly in degrees
    #
    #         # Insert satellite
    #         satellite = scenario.Children.New(
    #             AgESTKObjectType.eSatellite, f"Sat{orbitPlaneNum}{satNum}"
    #         )
    #
    #         # Select Propagator
    #         satellite.SetPropagatorType(AgEVePropagatorType.ePropagatorTwoBody)
    #
    #         # Set initial state
    #         twoBodyPropagator = satellite.Propagator
    #         keplerian = twoBodyPropagator.InitialState.Representation.ConvertTo(
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
    #         keplerian.Location.Value = trueAnomaly + (360 // numSatsPerPlane / 2) * (
    #                 orbitPlaneNum % 2
    #         )  # Stagger true anomalies (degrees) for every other orbital plane
    #
    #         # Propagate
    #         satellite.Propagator.InitialState.Representation.Assign(keplerian)
    #         satellite.Propagator.Propagate()
    #
    #         # Add to constellation object
    #         constellation.Objects.AddObject(satellite)
    #
    # stkRoot.EndUpdate()
    # # Create faciliy
    # facility = scenario.Children.New(AgESTKObjectType.eFacility, "MyFacility")
    # # Set position
    # facility.Position.AssignGeodetic(28.62, -80.62, 0.03)
    #
    # ############################################################################
    # # Chains
    # ############################################################################
    # # Create fac to sat Chain
    # chain = scenario.Children.New(AgESTKObjectType.eChain, "Chain")
    #
    # # Add satellite constellation and facility
    # chain.Objects.AddObject(constellation)
    # chain.Objects.AddObject(facility)

    # create chain
    all_satellites = scenario.Children.GetElements(AgESTKObjectType.eSatellite)
    for orbitPlaneNum in range(1, numOrbitPlanes + 1):
        for satNum in range(1, numSatsPerPlane + 1):
            cur_sat_name = f"Sat{orbitPlaneNum}{satNum}"
            inter_sat_name = f"Sat{orbitPlaneNum}{satNum + 1}"
            intra_sat_name = f"Sat{orbitPlaneNum + 1}{satNum}"
            # cur_sat = next(sat for sat in all_satellites if sat.InstanceName == cur_sat_name)
            if satNum == numSatsPerPlane:
                inter_sat_name = f"Sat{orbitPlaneNum}1"
            if orbitPlaneNum == numOrbitPlanes:
                intra_sat_name = f"Sat1{satNum}"
            print(f"current:{cur_sat_name}, previous:{inter_sat_name}, next:{intra_sat_name}")


    # # Compute chain
    # chain.ComputeAccess()
    #
    # # Find satellite with most access time
    # chainDataProvider = chain.DataProviders.GetDataPrvIntervalFromPath("Object Access")
    # chainResults = chainDataProvider.Exec(scenario.StartTime, scenario.StopTime)
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

    # 调用函数创建链路并输出距离信息
    # create_and_output_chains(constellation, scenario, numOrbitPlanes, numSatsPerPlane)

    # Print computation time
    totalTime = time.time() - startTime
    sectionTime = time.time() - splitTime
    splitTime = time.time()
    print(
        "--- Chain computation: {a:4.2f} sec\t\tTotal time: {b:4.2f} sec ---".format(
            a=sectionTime, b=totalTime
        )
    )

    # close STK
    # stkRoot.CloseScenario()
    # stk.ShutDown()
    # print("\nClosed STK successfully.")

    # stkRoot.CloseScenario()
    # stk.ShutDown()
    #
    # print("\nClosed STK successfully.")
    # 定义一个函数来创建并计算链路距离

# def create_and_output_chains(constellation, scenario, numOrbitPlanes, numSatsPerPlane):
#     all_satellites = scenario.Children.GetElements(AgESTKObjectType.eSatellite)
#     for orbitPlaneNum in range(1, numOrbitPlanes + 1):
#         for satNum in range(1, numSatsPerPlane + 1):
#             current_sat_name = f"Sat{orbitPlaneNum}{satNum}"
#             current_sat = next(sat for sat in all_satellites if sat.InstanceName == current_sat_name)
#             previous_sat_name = f"Sat{orbitPlaneNum}{(2*satNum - 1) % numSatsPerPlane}"
#             next_sat_name = f"Sat{orbitPlaneNum}{(satNum + 1) % numSatsPerPlane}"
#             previous_sat = next(sat for sat in all_satellites if sat.InstanceName == previous_sat_name)
#             next_sat = next(sat for sat in all_satellites if sat.InstanceName == next_sat_name)
#             if previous_sat and next_sat:
#                 create_and_compute_chain(scenario, previous_sat, current_sat, f"Chain_{previous_sat_name}_to_{current_sat_name}")
#                 create_and_compute_chain(scenario, current_sat, next_sat, f"Chain_{current_sat_name}_to_{next_sat_name}")


def compute_sat_access(scenario, sat1, sat2):
    # 计算两颗卫星之间的访问区间
    access = sat1.GetAccessToObject(sat2)
    access.ComputeAccess()

    # 获取访问区间数据提供者
    accessDP = access.DataProviders.Item('Access Data').Exec(scenario.StartTime, scenario.StopTime)

    # 从访问区间数据提供者中获取距离数据
    distances = accessDP.DataSets.GetDataSetByName('Distance').GetValues()

    # 打印距离数据
    for distance in distances:
        print(distance)


# 运行主程序
if __name__ == "__main__":
    main()

