# -*- coding: utf-8 -*-
# @Time    : 2024/4/13 16:51
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : stk_manager.py

import platform
import pandas as pd
import networkx as nx
from datetime import datetime
from src.utils.sim_config import *
from src.utils.tools import approx_time, get_time_list, generate_time_series
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
        # Close existing scenario if it exists
        if self.stk_root.CurrentScenario:
            self.stk_root.CloseScenario()
            
        # Create new scenario
        self.stk_root.NewScenario("new")
        self.scenario = self.stk_root.CurrentScenario
        self.scenario.SetTimePeriod(start_time, end_time)
        self.time_series = generate_time_series(start_time, end_time, time_step)
        # Initialize empty graph list for each time step
        self.graph_list = []
        for i in range(len(self.time_series)):
            # Create empty graph for each time step
            graph = nx.Graph()
            # Add time as graph attribute in ISO format
            graph.graph['time'] = self.time_series[i].isoformat()
            self.graph_list.append(graph)
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

                # add constrains for Satellite object
                accessConstraints = satellite.AccessConstraints
                cnstrAngle = accessConstraints.AddConstraint(29)
                cnstrAngle.Angle = 10.0

                # Add to list
                self.satellites.append(satellite)

                # Add satellite object to all graphs in graph_list
                for graph in self.graph_list:
                    if not graph.has_node(f"Sat{plane_num}_{sat_num}"):
                        graph.add_node(f"Sat{plane_num}_{sat_num}")

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

            # Add facility object to all graphs in graph_list
            for graph in self.graph_list:
                if not graph.has_node(name):
                    graph.add_node(name, latitude=latitude, longitude=longitude, altitude=altitude)

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
                        self.compute_sat_access(cur_sat, inter_sat)

                    if intra_sat:
                        self.compute_sat_access(cur_sat, intra_sat)

        except Exception as e:
            logger.error(f"Error in get_access: {e}")
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

        try:
            # Approximate time_origin using approx_time function
            matched_times = approx_time(time_origin, self.time_series)
            # logger.debug(f"Matched times from approx_time: {matched_times}")
            
            # Convert matched times to indices in time_series
            time_indices = [self.time_series.get_loc(t) for t in matched_times]
            logger.debug(f"Converted to indices: {time_indices}")
            
            # Check for missing indices
            all_indices = set(range(len(self.time_series)))
            missing_indices = sorted(all_indices - set(time_indices))
            if missing_indices:
                logger.debug(f"Missing indices: {missing_indices}")

            # Add range data as edge attribute to corresponding graphs
            for i, (time_idx, distance) in enumerate(zip(time_indices, sat_range)):
                # Get corresponding graph from graph_list
                graph = self.graph_list[time_idx]
                
                # Add range as edge attribute
                sat1_name = sat1.InstanceName
                sat2_name = sat2.InstanceName
                
                # Add edge with range attribute if it doesn't exist, update range if it does
                graph.add_edge(sat1_name, sat2_name, range=distance)
                # logger.debug(f"Added/updated range {distance} between {sat1_name} and {sat2_name} at time index {time_idx}")
        except KeyError as e:
            logger.error(f"Failed to find time index in time_series: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while processing range data: {e}")
            raise
        
    def save_graph_data(self):
        # 确保graphs目录存在
        graphs_dir = self.project_root / 'graphs'
        graphs_dir.mkdir(parents=True, exist_ok=True)
        
        for idx, graph in enumerate(self.graph_list):
            graph_path = graphs_dir / f'graph{idx}.json'
            with open(graph_path, 'w') as f:
                data = nx.node_link_data(graph)
                # indent=2 for more compact but still readable JSON formatting
                json.dump(data, f, indent=2)
            logger.info(f"Saved graph data to {graph_path}")

    # calculate distance between sat and fac
    # @timeit_decorator
    # def get_fac_access(self):
    #     try:
    #         if not self.constellation:
    #             raise Exception("Constellation object is not initialized.")
            
    #         # Dictionary to store data for each facility
    #         facility_data = {}
            
    #         for facility in self.facilities:
    #             facility_records = []  # List to store all records for current facility
                
    #             # Create chain object for satellite to facility
    #             sat_fac_chain = self.scenario.Children.New(AgESTKObjectType.eChain, f"Chain_{facility.InstanceName}")
                
    #             # Add satellite constellation and facility
    #             sat_fac_chain.Objects.AddObject(self.constellation)
    #             sat_fac_chain.Objects.AddObject(facility)
    #             sat_fac_chain.ComputeAccess()
                
    #             # Get data provider for range data as TimeVar
    #             rpt_elms = ["Time", "Strand Name", "Range"]
    #             chainDataProvider = sat_fac_chain.DataProviders.GetDataPrvTimeVarFromPath("Range Data")
    #             chainResults = chainDataProvider.ExecElements(
    #                 self.scenario.StartTime,
    #                 self.scenario.StopTime,
    #                 self.time_step,
    #                 rpt_elms
    #             )
                
    #             # Loop through all satellite access intervals
    #             for intervalNum in range(chainResults.Intervals.Count):
    #                 interval = chainResults.Intervals[intervalNum]
                    
    #                 # Get data for interval
    #                 chain_times = interval.DataSets.GetDataSetByName("Time").GetValues()
    #                 strand_names = interval.DataSets.GetDataSetByName("Strand Name").GetValues()
    #                 sat_fac_distances = interval.DataSets.GetDataSetByName("Range").GetValues()
                    
    #                 # Process time data
    #                 self.time_list = get_time_list()
    #                 chain_time_list = approx_time(chain_times, self.time_list)
                    
    #                 # Extract satellite name
    #                 sat_name, _ = self.extract_pattern_from_string(
    #                     strand_names[0],
    #                     pattern=r"\/(\w+)\s+To\s+.*\/(\w+)"
    #                 )
                    
    #                 # Add records for this interval
    #                 for time, distance in zip(chain_time_list, sat_fac_distances):
    #                     facility_records.append({
    #                         'Time': time,
    #                         'Satellite': sat_name,
    #                         'Facility': facility.InstanceName,
    #                         'Distance': round(distance)
    #                     })
                
    #             # Store all records for this facility
    #             facility_data[facility.InstanceName] = facility_records
            
    #         # Save data for each facility
    #         fac_sat_chains_path = self.data_directory / 'fac_sat_chains'
    #         fac_sat_chains_path.mkdir(parents=True, exist_ok=True)
            
    #         # Create separate CSV file for each facility
    #         for fac_name, records in facility_data.items():
    #             if records:  # Only create file if there are records
    #                 df = pd.DataFrame(records)
    #                 filepath = fac_sat_chains_path / f'{fac_name}_access_data.csv'
    #                 df.to_csv(filepath, index=False)
    #                 logger.info(f"Access data for {fac_name} saved to {filepath}")
            
    #         logger.info("All facility access data saved successfully")
        
    #     except Exception as e:
    #         logger.error(f"Error in get_fac_access: {e}")
    #         raise e


if __name__ == "__main__":
    pass