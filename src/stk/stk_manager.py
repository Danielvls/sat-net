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


class STKManager:
    def __init__(self):
        self.stk = None
        self.stk_root = None
        self.scenario = None
        self.time_list = []
        self.time_step = 300
        self.constellation = None
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
    def create_scenario(self, scenario_name, start_time, end_time):
        # Create new scenario
        self.stk_root.NewScenario(scenario_name)
        self.scenario = self.stk_root.CurrentScenario
        self.scenario.SetTimePeriod(start_time, end_time)
        if not self.use_stk_engine:
            # Graphics calls are not available when running STK Engine in NoGraphics mode
            self.stk_root.Rewind()

    @timeit_decorator
    def create_constellation(self) -> AgESTKObjectType:
        """Create a satellite constellation within the scenario."""
        self.constellation = self.scenario.Children.New(AgESTKObjectType.eConstellation, "IridiumConstellation")
        self.stk_root.BeginUpdate()
        for plane_num, RAAN in enumerate(
                range(0, 180, 180 // num_orbit_planes), start=1
        ):  # RAAN in degrees

            for sat_num in range(
                    1, 12
            ):  # trueAnomaly in degrees

                # Insert satellite
                satellite = self.scenario.Children.New(
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
                        # (sat_num - 1) * (360 / 11) + (plane_num - 1) * (360 / 66)
                        (sat_num - 1) * (360 / num_sat_per_plane) + (plane_num - 1) *
                        (360 / (num_orbit_planes * num_sat_per_plane))
                )  # true anomalies (degrees) for every other orbital plane

                # Propagate
                satellite.Propagator.InitialState.Representation.Assign(keplerian)
                satellite.Propagator.Propagate()

                # Add to constellation object
                self.constellation.Objects.AddObject(satellite)

        self.stk_root.EndUpdate()

    def create_facilities(self):
        """Create multiple facilities within the scenario and return them, using 3D coordinates."""

        # List of facility names and their geographical coordinates (latitude, longitude, altitude)
        facility_data = [
            ("Facility1", 28.62, -80.62, 10.0),  # 美国佛罗里达州
            ("Facility2", 34.30, 108.95, 400.0),  # 中国西安卫星测控中心
            ("Facility3", -23.80, 133.89, 600.0),  # 澳大利亚艾丽斯泉地面站
            ("Facility4", 47.83, 11.14, 600.0)  # 德国魏尔海姆跟踪站
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

    # creating access between satellites
    @timeit_decorator
    def create_access(self):
        unique_times = set()
        all_satellites = self.scenario.Children.GetElements(AgESTKObjectType.eSatellite)
        for plane_num in range(1, num_orbit_planes + 1):
            for sat_num in range(1, num_sat_per_plane + 1):
                cur_sat_name = f"Sat{plane_num}{sat_num}"

                # get satellites in the same orbital plane and the next orbital plane
                if plane_num < num_orbit_planes:
                    intra_sat_name = f"Sat{plane_num + 1}{sat_num}"
                    intra_sat = next(sat for sat in all_satellites if sat.InstanceName == intra_sat_name)
                else:
                    intra_sat_name = 0
                    intra_sat = 0

                if sat_num == num_sat_per_plane:
                    inter_sat_name = f"Sat{plane_num}1"
                else:
                    inter_sat_name = f"Sat{plane_num}{sat_num + 1}"

                # get satellites in the same orbital plane and the previous orbital plane
                cur_sat = next(sat for sat in all_satellites if sat.InstanceName == cur_sat_name)
                inter_sat = next(sat for sat in all_satellites if sat.InstanceName == inter_sat_name)

                # compute access between satellites
                if inter_sat:
                    sce_time, self.sat_distance[f"{cur_sat_name} to {inter_sat_name}"] = (
                        self.compute_sat_access(cur_sat, inter_sat)
                    )
                    unique_times.update(sce_time)
                if intra_sat:
                    sce_time, self.sat_distance[f"{cur_sat_name} to {intra_sat_name}"] = (
                        self.compute_sat_access(cur_sat, intra_sat)
                    )
                    unique_times.update(sce_time)
        self.time_list = list(unique_times)
        self.time_list.sort()
        self.time_list = [datetime.strptime(t.split('.')[0], '%d %b %Y %H:%M:%S') for t in self.time_list]
        self.compute_fac_access()
        self.save_data()

    # @timeit_decorator
    def compute_sat_access(self, sat1, sat2):
        access = sat1.GetAccessToObject(sat2)
        access.ComputeAccess()
        rpt_elms = ["Time", "Range"]
        access_DP = access.DataProviders.GetDataPrvTimeVarFromPath("AER Data/Default")
        access_result = access_DP.ExecElements(self.scenario.StartTime, self.scenario.StopTime, time_step, rpt_elms)
        time_origin = access_result.DataSets.GetDataSetByName('Time').GetValues()
        sat_range = access_result.DataSets.GetDataSetByName('Range').GetValues()
        return time_origin, sat_range

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

            # Get data provider for range data as TimeVar
            rpt_elms = ["Time", "Strand Name", "Range"]
            chainDataProvider = sat_fac_chain.DataProviders.GetDataPrvTimeVarFromPath("Range Data")
            chainResults = chainDataProvider.ExecElements(
                self.scenario.StartTime,
                self.scenario.StopTime,
                self.time_step,  # Ensure time_step is defined or passed to the function
                rpt_elms
            )
            # chainDataProvider = chain.DataProviders.GetDataPrvIntervalFromPath("Range Data")
            # chainResults = chainDataProvider.Exec(scenario.StartTime, scenario.StopTime, 300, rpt_elms)

            # Loop through all satellite access intervals
            for intervalNum in range(chainResults.Intervals.Count):
                # Get interval
                interval = chainResults.Intervals[intervalNum]

                # Get data for interval
                chain_times = interval.DataSets.GetDataSetByName("Time").GetValues()
                strand_names = interval.DataSets.GetDataSetByName("Strand Name").GetValues()
                sat_fac_distances = interval.DataSets.GetDataSetByName("Range").GetValues()

                # Process each data
                chain_times = self.truncate_times(chain_times)

                self.chain_time_list = self.approximate_time(chain_times)
                self.sat_fac_distances = self.round_distances(sat_fac_distances)
                self.sat_name, self.fac_name = self.extract_pattern_from_string(
                    strand_names[0],
                    pattern=r"\/(\w+)\s+To\s+.*\/(\w+)"
                )

                # Save satellite to facility chain data to csv file
                os.makedirs(f"{self.data_directory}/fac_sat_chains", exist_ok=True)
                processed_data = list(zip(self.chain_time_list, self.sat_fac_distances))
                distance_df = pd.DataFrame(processed_data, columns=['Time', 'Distance'])
                filepath = f'{self.data_directory}/fac_sat_chains/{self.sat_name} To {self.fac_name}.csv'
                distance_df.to_csv(filepath, index=False)
                # print(f"Data saved to {filepath}")

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
        distance_df.to_csv(f'{self.data_directory}/inter_satellite_distances.csv', index=False)

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
