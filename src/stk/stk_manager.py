# -*- coding: utf-8 -*-
# @Time    : 2024/4/13 16:51
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : stk_manager.py

import os
import platform
import pandas as pd
from datetime import datetime
from src.utils import *
import re


from agi.stk12.stkobjects import (
    AgEClassicalLocation,
    AgEClassicalSizeShape,
    AgEOrientationAscNode,
    AgESTKObjectType,
    AgEVePropagatorType,
)
from agi.stk12.stkdesktop import STKDesktop
from agi.stk12.stkutil import AgEOrbitStateType
import numpy as np

class STKManager:
    def __init__(self):
        self.stk = None
        self.stk_root = None
        self.scenario = None
        self.time_list = []
        self.time_step = 300
        self.constellation = None
        self.satellites = []
        self.facilities = []
        self.sat_distance = {}
        self.chain_time_list = []
        self.sat_fac_distances = []
        self.sat_name = ""
        self.fac_name = ""
        self.data_directory = '../data'
        if platform.system() == "Linux":
            # Only STK Engine is available on Linux
            self.use_stk_engine = True
        else:
            # Change to true to run engine on Windows
            self.use_stk_engine = False

    @timeit_decorator
    def launch_stk(self):
        if self.use_stk_engine:
            from agi.stk12.stkengine import STKEngine

            # Launch STK Engine with NoGraphics mode
            print("Launching STK Engine...")
            self.stk = STKEngine.StartApplication(noGraphics=True)

            # Create root object
            self.stk_root = self.stk.NewObjectRoot()

        else:
            from agi.stk12.stkdesktop import STKDesktop

            # Launch GUI
            print("Launching STK...")
            self.stk = STKDesktop.StartApplication(visible=True, userControl=True)

            # Get root object
            self.stk_root = self.stk.Root

    @timeit_decorator
    def attach_to_application(self):
        self.stk = STKDesktop.AttachToApplication()
        self.stk_root = self.stk.Root
        self.stk_root.UnitPreferences.SetCurrentUnit("DateFormat", "UTCG")

    @timeit_decorator
    def load_scenario(self, scenario_path, start_time, end_time):
        self.stk_root.LoadScenario(scenario_path)
        self.scenario = self.stk_root.CurrentScenario
        self.scenario.SetTimePeriod(start_time, end_time)
        if not self.use_stk_engine:
            # Graphics calls are not available when running STK Engine in NoGraphics mode
            self.stk_root.Rewind()

    @timeit_decorator
    def create_scenario(self, start_time, end_time):
        # Create new scenario
        self.stk_root.NewScenario("new")
        self.scenario = self.stk_root.CurrentScenario
        self.scenario.SetTimePeriod(start_time, end_time)
        if not self.use_stk_engine:
            # Graphics calls are not available when running STK Engine in NoGraphics mode
            self.stk_root.Rewind()

    @timeit_decorator
    def create_constellation(self, constellation_name) -> AgESTKObjectType:
        """Create a satellite constellation within the scenario."""
        self.constellation = self.scenario.Children.New(AgESTKObjectType.eConstellation, constellation_name)
        self.stk_root.BeginUpdate()

        true_anomalies = np.linspace(0, 360, num_sat_per_plane, endpoint=False)
        RAANs = np.linspace(0, 360, num_orbit_planes, endpoint=False)

        for plane_num, RAAN in enumerate(RAANs, start=1):  # RAAN in degrees
            true_anomalies = (true_anomalies + (360/T)*F) % 360
            for sat_num, trueAnomaly in enumerate(true_anomalies, start=1):  # trueAnomaly in degrees
                # Insert satellite
                satellite = self.scenario.Children.New(
                    AgESTKObjectType.eSatellite, f"Sat{plane_num}_{sat_num}"
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
                keplerian.SizeShape.SemiMajorAxis = height  # km
                keplerian.SizeShape.Eccentricity = 0
                keplerian.Orientation.Inclination = inc  # degrees
                keplerian.Orientation.ArgOfPerigee = 0  # degrees
                keplerian.Orientation.AscNode.Value = RAAN  # degrees
                keplerian.Location.Value = trueAnomaly

                # Propagate
                satellite.Propagator.InitialState.Representation.Assign(keplerian)
                satellite.Propagator.Propagate()

                # Add to list
                self.satellites.append(satellite)
                # Add to constellation object
                self.constellation.Objects.AddObject(satellite)

        self.stk_root.EndUpdate()

    def create_facilities(self):
        """Create multiple facilities within the scenario and return them, using 3D coordinates."""

        # List of facility names and their geographical coordinates (latitude, longitude, altitude)
        facility_data = [
            ("Facility1", 34.0522, -118.2437, 85.0),  # 美国洛杉矶
            ("Facility2", -33.8688, 151.2093, 85.0),  # 澳大利亚悉尼
            ("Facility3", 51.5074, -0.1278, 85.0),  # 英国伦敦
            ("Facility4", 48.8566, 2.3522, 85.0),  # 法国巴黎
            ("Facility5", 40.7128, -74.0060, 85.0),  # 美国纽约
            ("Facility6", 39.9042, 116.4074, 85.0),  # 中国北京
            ("Facility7", -23.5505, -46.6333, 85.0),  # 巴西圣保罗
            ("Facility8", 35.6895, 139.6917, 85.0),  # 日本东京
            ("Facility9", 55.7558, 37.6173, 85.0),  # 俄罗斯莫斯科
            ("Facility10", -34.6037, -58.3816, 85.0),  # 阿根廷布宜诺斯艾利斯
            # ("Facility11", 40.7306, -73.9352, 85.0),  # 美国纽约（偏北）
            # ("Facility12", 52.3676, 4.9041, 85.0),  # 荷兰阿姆斯特丹
            # ("Facility13", 37.9838, 23.7275, 85.0),  # 希腊雅典
            # ("Facility14", 19.4326, -99.1332, 85.0),  # 墨西哥墨西哥城
            # ("Facility15", 43.6532, -79.3832, 85.0),  # 加拿大多伦多
            # ("Facility16", 1.3521, 103.8198, 85.0),  # 新加坡
            # ("Facility17", 55.6761, 12.5683, 85.0),  # 丹麦哥本哈根
            # ("Facility18", 37.7749, -122.4194, 85.0),  # 美国旧金山
            # ("Facility19", 40.7306, -73.9352, 85.0),  # 美国纽约（偏南）
            # ("Facility20", 51.1657, 10.4515, 85.0),  # 德国
        ]

        # Loop through each entry in the facility data
        for name, latitude, longitude, altitude in facility_data:
            # Create facility
            facility = self.scenario.Children.New(AgESTKObjectType.eFacility, name)

            # Set position with altitude
            facility.Position.AssignGeodetic(latitude, longitude, altitude)

            # Add the facility to the list
            self.facilities.append(facility)

        # # maybe worth trying to use the STK API for this
        # facility = self.scenario.Children.New(AgESTKObjectType.eFacility, name)
        # facility.SetPosition(lat, lon, alt)
        # return facility

    @timeit_decorator
    def create_access(self):
        unique_times = set()

        # 获取所有卫星对象并将其按 InstanceName 存入字典
        all_satellites = self.scenario.Children.GetElements(AgESTKObjectType.eSatellite)
        satellite_dict = {sat.InstanceName: sat for sat in all_satellites}
        # print(satellite_dict)

        for plane_num in range(1, num_orbit_planes + 1):
            for sat_num in range(1, num_sat_per_plane + 1):
                cur_sat_name = f"Sat{plane_num}_{sat_num}"
                cur_sat = satellite_dict.get(cur_sat_name)
                if not cur_sat:
                    break  # 如果未找到该卫星，可以选择跳过或者处理缺失的情况

                # get satellite in adjacent orbit for current satellite
                if plane_num < num_orbit_planes:
                    inter_sat_name = f"Sat{plane_num + 1}_{sat_num}"
                else:
                    print(f"this is {cur_sat_name} trying to connect Sat1_{int((sat_num + F) % (T / P)) or int(T / P)}")
                    inter_sat_name = f"Sat1_{int((sat_num + F) % (T / P)) or int(T / P)}"
                inter_sat = satellite_dict.get(inter_sat_name)

                # get satellite in same orbit for current satellite
                if sat_num == num_sat_per_plane:
                    intra_sat_name = f"Sat{plane_num}_1"
                else:
                    intra_sat_name = f"Sat{plane_num}_{sat_num + 1}"
                intra_sat = satellite_dict.get(intra_sat_name)

                # compute access between satellites
                if inter_sat:
                    # sce_time, self.sat_distance[f"{cur_sat_name} to {inter_sat_name}"] = (
                    self.compute_sat_access(cur_sat, inter_sat)
                    # )
                    # unique_times.update(sce_time)
                if intra_sat:
                    # sce_time, self.sat_distance[f"{cur_sat_name} to {intra_sat_name}"] = (
                    self.compute_sat_access(cur_sat, intra_sat)
                    # )
        # self.time_list = list(unique_times)
        # self.time_list.sort()
        # self.time_list = [datetime.strptime(t.split('.')[0], '%d %b %Y %H:%M:%S') for t in self.time_list]
        # self.compute_fac_access()
        # self.save_data()

    #
    # # creating access between satellites
    # @timeit_decorator
    # def create_access(self):
    #     unique_times = set()
    #     all_satellites = self.scenario.Children.GetElements(AgESTKObjectType.eSatellite)
    #     for plane_num in range(1, num_orbit_planes + 1):
    #         for sat_num in range(1, num_sat_per_plane + 1):
    #             cur_sat_name = f"Sat{plane_num}_{sat_num}"
    #             cur_sat = next(sat for sat in all_satellites if sat.InstanceName == cur_sat_name)
    #
    #             # get satellite in adjacent orbit for current satellite
    #             if plane_num < num_orbit_planes:
    #                 inter_sat_name = f"Sat{plane_num + 1}_{sat_num}"
    #                 inter_sat = next(sat for sat in all_satellites if sat.InstanceName == inter_sat_name)
    #             else:
    #                 inter_sat_name = f"Sat0_{sat_num}"
    #                 inter_sat = next(sat for sat in all_satellites if sat.InstanceName == inter_sat_name)
    #
    #             # get satellite in same orbit for current satellite
    #             if sat_num == num_sat_per_plane:
    #                 intra_sat_name = f"Sat{plane_num}_1"
    #             else:
    #                 intra_sat_name = f"Sat{plane_num}_{sat_num + 1}"
    #
    #             # compute access between satellites
    #             if inter_sat:
    #                 sce_time, self.sat_distance[f"{cur_sat_name} to {inter_sat_name}"] = (
    #                     self.compute_sat_access(cur_sat, inter_sat)
    #                 )
    #                 unique_times.update(sce_time)
    #             if intra_sat:
    #                 sce_time, self.sat_distance[f"{cur_sat_name} to {intra_sat_name}"] = (
    #                     self.compute_sat_access(cur_sat, intra_sat)
    #                 )
    #
    #
    #
    #
    #             if plane_num < num_orbit_planes:
    #                 inter_sat_name = f"Sat{plane_num + 1}_{sat_num}"
    #                 inter_sat = next(sat for sat in all_satellites if sat.InstanceName == inter_sat_name)
    #             else:
    #                 inter_sat_name = 0
    #                 inter_sat = 0
    #
    #             if sat_num == num_sat_per_plane:
    #                 intra_sat_name = f"Sat{plane_num}_1"
    #             else:
    #                 intra_sat_name = f"Sat{plane_num}_{sat_num + 1}"
    #
    #             # get satellites in the same orbital plane and the previous orbital plane
    #             cur_sat = next(sat for sat in all_satellites if sat.InstanceName == cur_sat_name)
    #             intra_sat = next(sat for sat in all_satellites if sat.InstanceName == intra_sat_name)
    #
    #             # compute access between satellites
    #             if inter_sat:
    #                 sce_time, self.sat_distance[f"{cur_sat_name} to {inter_sat_name}"] = (
    #                     self.compute_sat_access(cur_sat, inter_sat)
    #                 )
    #                 unique_times.update(sce_time)
    #             if intra_sat:
    #                 sce_time, self.sat_distance[f"{cur_sat_name} to {intra_sat_name}"] = (
    #                     self.compute_sat_access(cur_sat, intra_sat)
    #                 )
    #                 unique_times.update(sce_time)
    #     self.time_list = list(unique_times)
    #     self.time_list.sort()
    #     self.time_list = [datetime.strptime(t.split('.')[0], '%d %b %Y %H:%M:%S') for t in self.time_list]
    #     self.compute_fac_access()
    #     self.save_data()

    # @timeit_decorator
    def compute_sat_access(self, sat1, sat2):
        access = sat1.GetAccessToObject(sat2)
        access.ComputeAccess()
        # rpt_elms = ["Time", "Range"]
        # access_DP = access.DataProviders.GetDataPrvTimeVarFromPath("AER Data/Default")
        # access_result = access_DP.ExecElements(self.scenario.StartTime, self.scenario.StopTime, time_step, rpt_elms)
        # time_origin = access_result.DataSets.GetDataSetByName('Time').GetValues()
        # sat_range = access_result.DataSets.GetDataSetByName('Range').GetValues()
        # return time_origin, sat_range

    # calculate distance between sat and fac
    @timeit_decorator
    def compute_fac_access(self):
        if not self.constellation:
            raise Exception("Constellation object is not initialized.")
        for facility in self.facilities:

            # Create chain object for satellite to facility
            sat_fac_chain = self.scenario.Children.New(AgESTKObjectType.eChain, f"Chain_{facility.InstanceName}")

            # Add satellite constellation and facility
            sat_fac_chain.Objects.AddObject(self.constellation)
            sat_fac_chain.Objects.AddObject(facility)
            sat_fac_chain.ComputeAccess()
            #
            # # Get data provider for range data as TimeVar
            # rpt_elms = ["Time", "Strand Name", "Range"]
            # chainDataProvider = sat_fac_chain.DataProviders.GetDataPrvTimeVarFromPath("Range Data")
            # chainResults = chainDataProvider.ExecElements(
            #     self.scenario.StartTime,
            #     self.scenario.StopTime,
            #     self.time_step,  # Ensure time_step is defined or passed to the function
            #     rpt_elms
            # )
            # # chainDataProvider = chain.DataProviders.GetDataPrvIntervalFromPath("Range Data")
            # # chainResults = chainDataProvider.Exec(scenario.StartTime, scenario.StopTime, 300, rpt_elms)
            #
            # # Loop through all satellite access intervals
            # for intervalNum in range(chainResults.Intervals.Count):
            #     # Get interval
            #     interval = chainResults.Intervals[intervalNum]
            #
            #     # Get data for interval
            #     chain_times = interval.DataSets.GetDataSetByName("Time").GetValues()
            #     strand_names = interval.DataSets.GetDataSetByName("Strand Name").GetValues()
            #     sat_fac_distances = interval.DataSets.GetDataSetByName("Range").GetValues()
            #
            #     # Process each data
            #     chain_times = self.truncate_times(chain_times)
            #
            #     self.chain_time_list = self.approximate_time(chain_times)
            #     self.sat_fac_distances = self.round_distances(sat_fac_distances)
            #     self.sat_name, self.fac_name = self.extract_pattern_from_string(
            #         strand_names[0],
            #         pattern=r"\/(\w+)\s+To\s+.*\/(\w+)"
            #     )
            #
            #     # Save satellite to facility chain data to csv file
            #     os.makedirs(f"{self.data_directory}/fac_sat_chains", exist_ok=True)
            #     processed_data = list(zip(self.chain_time_list, self.sat_fac_distances))
            #     distance_df = pd.DataFrame(processed_data, columns=['Time', 'Distance'])
            #     filepath = f'{self.data_directory}/fac_sat_chains/{self.sat_name} To {self.fac_name}.csv'
            #     distance_df.to_csv(filepath, index=False)
            #     # print(f"Data saved to {filepath}")

    def get_sat_lla(self):
        for sat in self.satellites:
            rpt_elms = ["Time", "Lat", "Lon"]
            sat_lla = []
            sat_name = sat.InstanceName
            chainDataProvider = sat.DataProviders.GetDataPrvTimeVarFromPath("LLA State/TrueOfDateRotating")
            chainResults = chainDataProvider.ExecElements(
                self.scenario.StartTime,
                self.scenario.StopTime,
                self.time_step,  # Ensure time_step is defined or passed to the function
                rpt_elms
            )

            for i in range(len(chainResults.DataSets.GetDataSetByName("Time").GetValues())):
                sat_time = chainResults.DataSets.GetDataSetByName("Time").GetValues()[i]
                lat = chainResults.DataSets.GetDataSetByName("Lat").GetValues()[i]
                lon = chainResults.DataSets.GetDataSetByName("Lon").GetValues()[i]
                sat_lla.append([sat_time, lat, lon])

            # Save satellite LLA data to CSV file
            os.makedirs(f"{self.data_directory}/sat_lla_reports", exist_ok=True)
            lla_df = pd.DataFrame(sat_lla, columns=['Time', 'Latitude', 'Longitude'])
            filepath = f"{self.data_directory}/sat_lla_reports/{sat_name}_lla.csv"
            lla_df.to_csv(filepath, index=False)
            print(f"Saved LLA data for {sat_name} to {filepath}")

    # Truncate the given time string to remove microseconds or smaller units.
    @staticmethod
    def truncate_times(chain_times, format_str="%d %b %Y %H:%M:%S") -> list:
        dt_times = []
        for time_str in chain_times:
            if '.' in time_str:
                time_str = time_str[:time_str.rfind('.')]
            dt_time = datetime.strptime(time_str, format_str)
            dt_times.append(dt_time)
        return dt_times

    @staticmethod
    def round_distances(distances):
        return [round(distance) for distance in distances]

    @staticmethod
    def extract_pattern_from_string(input_string, pattern, default='Unknown'):
        # Extracts a specific pattern from the given string using regular expressions.
        match = re.search(pattern, input_string)
        if match:
            return match.group(1), match.group(2)
        else:
            return default, default

    def approximate_time(self, time_origin) -> list:
        approximated_times = []
        for time_temp in time_origin:
            approx_time = None
            for tl_time in self.time_list:
                if tl_time > time_temp:
                    break
                approx_time = tl_time
            if approx_time is not None:
                approximated_times.append(approx_time)
        return approximated_times

    # save data to csv files
    @timeit_decorator
    def save_data(self):
        if not os.path.exists(self.data_directory):
            os.makedirs(self.data_directory)
        distance_data = []

        # save satellite distance data to csv file
        for satellite_pair, distance_list in self.sat_distance.items():
            for distance in distance_list:
                distance_data.append([satellite_pair, distance])
        distance_df = pd.DataFrame(distance_data, columns=['SatellitePair', 'Distance'])
        distance_df.to_csv(f'{self.data_directory}/aer_data/inter_satellite_distances.csv', index=False)

        # save time series data to csv file
        time_series = pd.Series(self.time_list, name='Time Series')
        time_series.to_csv(f'{self.data_directory}/time_series.csv', index=False)


if __name__ == "__main__":
    manager = STKManager()
    manager.attach_to_application()
    manager.load_scenario('D:/STKScenario/star_blank/star.sc',
                          "1 Aug 2020 16:00:00", "1 Aug 2020 16:30:00")
    manager.create_constellation()
    manager.create_facilities()
    manager.create_access()
    manager.save_data()
