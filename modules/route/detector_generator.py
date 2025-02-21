import os
import xml.etree.ElementTree as ET
import pandas as pd
from modules.core.app_context import AppContext
from modules.core.network_base import NetworkBase
from modules.network.network_parser import NetworkParser
from modules.common.utils import XMLFile


"""  
This script is used to generate detectors for the network.
The detector types are induction loops, lanearea detectors, and multi-entry/multi-exit detectors.
"""

class DetectorGenerator(NetworkBase):
    """Generates network detectors.

    Args:
        app_context (AppContext): Central application context.
    """
    def __init__(self, app_context: AppContext) -> None:
        """
        Initialize the detector manager.

        Args:
            config_path (str): Path to the configuration file.
        """
        super().__init__(app_context)
        self.network_parser = NetworkParser(self.net_file, self.logger)

    def generate_induction_loops(self) -> None:
        """Generates induction loops for the network."""
        output_file = os.path.join(self.network_outputs, "e1_detectors.add.xml")
        results_file = "e1output.xml"

        # Generate XML file
        XMLFile.create_xml_file("additional", results_file)

        distance = self.detector_settings['induction_loop_detectors']['distance']
        frequency = self.detector_settings['induction_loop_detectors']['frequency']
        tool_e1 = os.path.join(self.sumo_tools_path, "output", "generateTLSE1Detectors.py")

        command = [
            "python", tool_e1,
            "-n", self.net_file,
            "-d", str(distance),
            "-f", str(frequency),
            "-o", output_file,
            "-r", results_file
        ]

        self.logger.info(f"Induction Loop Command: {' '.join(command)}")
        self.executor.run_command(command)
        
    def generate_lanearea_detectors(self) -> None:
        """Generates lanearea detectors for the network."""
        output_file = os.path.join(self.network_outputs, "initial_e2_detectors.add.xml")
        results_file = "e2output.xml"


        XMLFile.create_xml_file(results_file, "additional")

        detector_length = self.detector_settings['lanearea_detectors']['detector_length']
        distance = self.detector_settings['lanearea_detectors']['distance']
        frequency = self.detector_settings['lanearea_detectors']['frequency']
        tool_e2 = os.path.join(self.sumo_tools_path, "output", "generateTLSE2Detectors.py")

        # For implicit definition, set endPos = lane length and length = endPos-startPos

        command = [
            "python", tool_e2,
            "-n", self.net_file,
            # "-d", str(distance),
            # "-l", str(detector_length),
            "-f", str(frequency),
            "-o", output_file,
            "-r", results_file
        ]
        
        if self.detector_settings['lanearea_detectors']['tl_coupled']:
            command.append("--tl-coupled")
        
        self.logger.info(f"Lanearea Detector Command: {' '.join(command)}")
        self.executor.run_command(command)
        
    def generate_multi_entry_exit_detectors(self) -> None:
        """Generates multi-entry/multi-exit detectors for the network."""
        output_file = os.path.join(self.network_outputs, "e3_detectors.add.xml")
        results_file = "e3output.xml"


        XMLFile.create_xml_file(results_file, "additional")

        distance = self.detector_settings['multi_entry_exit_detectors']['distance']
        min_position = self.detector_settings['multi_entry_exit_detectors']['min_position']
        frequency = self.detector_settings['multi_entry_exit_detectors']['frequency']
        # junction_ids = self._get_junction_ids()
        # junction_ids = self.network_parser.get_junction_ids()
        tool_e3 = os.path.join(self.sumo_tools_path, "output", "generateTLSE3Detectors.py")


        command = [
            "python", tool_e3,
            "-n", self.net_file,
            "-j", self.junction_ids,
            "-d", str(distance),
            "-f", str(frequency),
            "--min-pos", str(min_position),
            "-o", output_file,
            "-r", results_file
        ]
        
        if self.detector_settings['multi_entry_exit_detectors']['joined']:
            command.append("--joined")
        if self.detector_settings['multi_entry_exit_detectors']['interior']:
            command.append("--interior")
        if self.detector_settings['multi_entry_exit_detectors']['follow_turnaround']:
            command.append("--follow-turnaround")
        
        self.logger.info(f"Multi-Entry/Exit Detector Command: {' '.join(command)}")
        self.executor.run_command(command)

    def get_lane_length(self, lane_id: str) -> float:
        """Retrieves lane length by lane ID.

        Args:
            lane_id (str): The lane ID.

        Returns:
            float: The lane length.
        """
        edge_id = lane_id.split('_')[0]

        # If it's a negative edge, strip the negative sign to find the matching positive edge
        is_negative = edge_id.startswith('-')
        if is_negative:
            edge_id = edge_id[1:]

        # Check in the edges dictionary (which contains both positive and negative lanes)
        lane_length = 0
        if edge_id in self.edges:
            for lane in self.edges[edge_id]['lanes']:
                # Adjust lane ID for negative lanes
                current_lane_id = '-' + lane['id'] if is_negative else lane['id']
                if current_lane_id == lane_id:
                    lane_length = lane['length']
                    break

        return lane_length


    def modify_detectors(self) -> None:
        """Modifies lanearea detectors XML file for safe positioning."""
        file_path = os.path.join(self.network_outputs, "initial_e2_detectors.add.xml")
        output_path = os.path.join(self.network_outputs, "e2_detectors.add.xml")



        tree = ET.parse(file_path)
        root = tree.getroot()

        for detector in root.findall('.//laneAreaDetector'):
            # Set the initial position of the detector (0.1 meters from the start of the lane)
            detector.set('pos', '0.1')

            # Get lane length
            lane_id = detector.get('lane')
            lane_length = self.get_lane_length(lane_id)  # function to fetch lane lengths

            # Calculate maximum detector length based on the lane length
            pos = float(detector.get('pos'))
            max_length = round((lane_length - pos), 2)
            adjusted_length = max_length - 1.0  # Leave a 1 meter buffer
            # Set a safe detector length (slightly less than the max length)
            # adjusted_length = min(float(detector.get('length')), max_length) - 1.0  # Leave a 1 meter buffer

            # Cap the adjusted length if needed
            if adjusted_length > 200:
                adjusted_length = 200  # Cap the length at 200 meters
            
            # Avoid negative lengths
            if adjusted_length < 0:
                adjusted_length = 0.1

            detector.set('length', str(adjusted_length))

            # Ensure friendlyPos is set to 'true' for better error handling
            detector.set('friendlyPos', 'true')

        tree.write(output_path, encoding='utf-8', xml_declaration=True)


    def _get_junction_ids(self) -> str:
        """Retrieves a comma-separated list of junction IDs.

        Returns:
            str: Junction IDs.
        """
        node_junction_mapping_file = os.path.join(self.processing_outputs, 'node_junction_mapping.csv')
        node_junction_mapping = pd.read_csv(node_junction_mapping_file)
        junction_ids = node_junction_mapping['junction_id'].unique()
        return ','.join(map(str, junction_ids))


    def execute_detector_generation(self) -> None:
        """Executes all detector generation tasks."""
        self.network_parser.load_network()
        self.edges = self.network_parser.edges
        junctions = self.network_parser.junctions
        junction_ids = list(junctions.keys())
        self.junction_ids = ','.join(map(str, junction_ids))

        if self.detector_settings['generate_induction_loops']:
            self.logger.info("Generating induction loops...")
            self.generate_induction_loops()
            self.logger.info("End of induction loop generation process.")
        
        if self.detector_settings['generate_lanearea_detectors']:
            self.logger.info("Generating lanearea detectors...")
            self.generate_lanearea_detectors()
            self.logger.info("End of lanearea detector generation process.")
        
        if self.detector_settings['lanearea_detectors']['modify_lanearea_detectors']:
            self.logger.info("Modifying lanearea detectors...")
            self.modify_detectors()
            self.logger.info("End of lanearea detector modification process.")
            
        if self.detector_settings['generate_multi_entry_exit_detectors']:
            self.logger.info("Generating multi-entry/multi-exit detectors...")
            self.generate_multi_entry_exit_detectors()
            self.logger.info("End of multi-entry/multi-exit detector generation process.")
        
        self.logger.info("Detector Generation Completed.")
        self.logger.info(f"\n.......................\n")
        

    def execute(self) -> None:
        """Task entry-point: executes detector generation."""
        self.execute_detector_generation()



