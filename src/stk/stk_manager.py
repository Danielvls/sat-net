# -*- coding: utf-8 -*-
# @Time    : 2024/4/13 16:51
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : stk_manager.py

import platform
import pandas as pd
from datetime import datetime
from src.utils.sim_config import *
from src.utils.tools import truncate_times
import re
import json
import numpy as np
from pathlib import Path

from agi.stk12.stkobjects import (
    AgEClassicalLocation,
    AgEClassicalSizeShape,
    AgEOrientationAscNode,
    AgESTKObjectType,
    AgEVePropagatorType,
)
from agi.stk12.stkdesktop import STKDesktop
from agi.stk12.stkutil import AgEOrbitStateType
from src.utils import Logger

logger = Logger().get_logger()

class STKManager:
    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[2]
        self.data_directory = self.project_root / 'data'
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
        if platform.system() == "Linux":
            # Only STK Engine is available on Linux
            self.use_stk_engine = True
        else:
            # Change to true to run engine on Windows
            self.use_stk_engine = False

    def launch_stk(self):
        if self.use_stk_engine:
            from agi.stk12.stkengine import STKEngine

            # Launch STK Engine with NoGraphics mode
            logger.info("Launching STK Engine...")
            self.stk = STKEngine.StartApplication(noGraphics=True)

            # Create root object
            self.stk_root = self.stk.NewObjectRoot()

        else:
            from agi.stk12.stkdesktop import STKDesktop

            # Launch GUI
            logger.info("Launching STK...")
            self.stk = STKDesktop.StartApplication(visible=True, userControl=True)

            # Get root object
            self.stk_root = self.stk.Root

    def attach_to_application(self):
        logger.info("Attaching to STK application...")
        self.stk = STKDesktop.AttachToApplication()
        self.stk_root = self.stk.Root
        self.stk_root.UnitPreferences.SetCurrentUnit("DateFormat", "UTCG")

    def load_scenario(self, scenario_path, start_time, end_time):
        self.stk_root.LoadScenario(scenario_path)
        self.scenario = self.stk_root.CurrentScenario
        self.scenario.SetTimePeriod(start_time, end_time)
        if not self.use_stk_engine:
            # Graphics calls are not available when running STK Engine in NoGraphics mode
            self.stk_root.Rewind()

    def create_scenario(self, start_time, end_time):
        # Create new scenario
        self.stk_root.NewScenario("new")
        self.scenario = self.stk_root.CurrentScenario
        self.scenario.SetTimePeriod(start_time, end_time)
        if not self.use_stk_engine:
            # Graphics calls are not available when running STK Engine in NoGraphics mode
            self.stk_root.Rewind()

    def create_constellation(self, constellation_name):
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

                # # add constrains for Satellite object
                # accessConstraints = satellite.AccessConstraints

                # # IAgAccessConstraintCollection accessConstraints: Access Constraint collection
                # # Angle constraint
                # cnstrAngle = accessConstraints.AddConstraint(29)
                # cnstrAngle.Angle = 5.0

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

    def get_sat_access(self):
        sce_time = []

        # get all satellites in the scenario and create a dictionary mapping satellite names to satellite objects
        all_satellites = self.scenario.Children.GetElements(AgESTKObjectType.eSatellite)
        satellite_dict = {sat.InstanceName: sat for sat in all_satellites}

        try:
            for plane_num in range(1, num_orbit_planes + 1):
                for sat_num in range(1, num_sat_per_plane + 1):
                    cur_sat_name = f"Sat{plane_num}_{sat_num}"
                    cur_sat = satellite_dict.get(cur_sat_name)
                    if not cur_sat:
                        break

                    # get satellite in adjacent orbit for current satellite
                    if plane_num < num_orbit_planes:
                        inter_sat_name = f"Sat{plane_num + 1}_{sat_num}"
                    else:
                        # print(f"this is {cur_sat_name} trying to connect Sat1_{int((sat_num + F) % (T / P)) or int(T / P)}")
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
                        _, self.sat_distance[f"{cur_sat_name} to {inter_sat_name}"] = (
                        self.compute_sat_access(cur_sat, inter_sat)
                        )
                        
                    if intra_sat:
                        sce_time, self.sat_distance[f"{cur_sat_name} to {intra_sat_name}"] = (
                        self.compute_sat_access(cur_sat, intra_sat)
                        )
        except Exception as e:
            logger.error(f"Error in get_access: {e}")
            raise e
        try:
            # Parse scenario time strings into datetime objects
            self.time_list = []
            for t in sce_time:
                try:
                    # Remove microseconds before parsing
                    time_str = t.split('.')[0]
                    dt = datetime.strptime(time_str, '%d %b %Y %H:%M:%S')
                    self.time_list.append(dt)
                except ValueError as e:
                    logger.error(f"Failed to parse time string: {t}")
                    raise e

            # Create data directory if it doesn't exist
            self.data_directory.mkdir(parents=True, exist_ok=True)
            
            # Save time series data to JSON file with datetime objects in ISO format
            time_file = self.data_directory / 'time_series.json'
            with open(time_file, 'w') as f:
                # Convert datetime objects to ISO format strings before serializing
                iso_times = [dt.isoformat() for dt in self.time_list]
                json.dump(iso_times, f, indent=4)
            logger.info(f"Parsed scenario time list saved to {time_file}")
        except Exception as e:
            logger.error(f"Error saving time list: {str(e)}")
            raise e
        try:
            # Reorganize distance data into quadruples (time, source, target, range)
            distance_data = []
            for satellite_pair, distance_list in self.sat_distance.items():
                source, target = satellite_pair.split(" to ")
                for time, distance in zip(self.time_list, distance_list):
                    distance_data.append([time, source, target, distance])

            # create dataframe
            distance_df = pd.DataFrame(
                distance_data, 
                columns=['Time', 'SourceSatellite', 'TargetSatellite', 'Distance']
            )

            # save to csv
            aer_folder_path = self.data_directory / 'aer_data'
            aer_folder_path.mkdir(parents=True, exist_ok=True)
            distance_file = aer_folder_path / 'inter_satellite_distances.csv'
            distance_df.to_csv(distance_file, index=False)
            logger.info(f"The inter-satellite distances data is saved to {distance_file}")
        except Exception as e:
            logger.error(f"Error in save_distance_data: {e}")
            raise e

    def get_sat_lla(self):
        try:
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
            lla_reports_path = self.data_directory / 'sat_lla_reports'
            lla_reports_path.mkdir(parents=True, exist_ok=True)
            lla_df = pd.DataFrame(sat_lla, columns=['Time', 'Latitude', 'Longitude'])
            filepath = lla_reports_path / f"{sat_name}_lla.csv"
            lla_df.to_csv(filepath, index=False)
            logger.info(f"Saved LLA data for {sat_name} to {filepath}")
        except Exception as e:
            logger.error(f"Error in get_sat_lla: {e}")
            raise e

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
    # @timeit_decorator
    def get_fac_access(self):
        try:
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
                    chain_times = truncate_times(chain_times)
                
                    self.chain_time_list = self.approximate_time(chain_times)
                    self.sat_fac_distances = self.round_distances(sat_fac_distances)
                    self.sat_name, self.fac_name = self.extract_pattern_from_string(
                        strand_names[0],
                            pattern=r"\/(\w+)\s+To\s+.*\/(\w+)"
                        )

                try:
                    # Save satellite to facility chain data to csv file
                    fac_sat_chains_path = self.data_directory / 'fac_sat_chains'
                    fac_sat_chains_path.mkdir(parents=True, exist_ok=True)
                    processed_data = list(zip(self.chain_time_list, self.sat_fac_distances))
                    distance_df = pd.DataFrame(processed_data, columns=['Time', 'Distance'])
                    filepath = fac_sat_chains_path / f'{self.sat_name} To {self.fac_name}.csv'
                    distance_df.to_csv(filepath, index=False)
                    # logger.info(f"satellite to facility chain data saved to {filepath}")
                except Exception as e:
                    logger.error(f"Error in save_fac_sat_chain_data: {e}")
                    raise e
            logger.info("satellite to facility chain data saved")
        except Exception as e:
            logger.error(f"Error in compute_fac_access: {e}")
            raise e
        try:
            # Save satellite to facility chain data to csv file
            fac_sat_chains_path = self.data_directory / 'fac_sat_chains'
            fac_sat_chains_path.mkdir(parents=True, exist_ok=True)
            processed_data = list(zip(self.chain_time_list, self.sat_fac_distances))
            distance_df = pd.DataFrame(processed_data, columns=['Time', 'Distance'])
            filepath = fac_sat_chains_path / f'{self.sat_name} To {self.fac_name}.csv'
            distance_df.to_csv(filepath, index=False)
            logger.info(f"satellite to facility chain data saved to {filepath}")
        except Exception as e:
            logger.error(f"Error in save_fac_sat_chain_data: {e}")
            raise e

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


if __name__ == "__main__":
    pass