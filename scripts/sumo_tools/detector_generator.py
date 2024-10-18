import os
import pandas as pd
from scripts.common.network_base import NetworkBase
from scripts.common.utils import XMLFile
import xml.etree.ElementTree as ET
from scripts.traffic_data_processing.network_parser import NetworkParser


"""  
This script is used to generate detectors for the network.
The detector types are induction loops, lanearea detectors, and multi-entry/multi-exit detectors.
"""

class DetectorGenerator(NetworkBase):
    def __init__(self, config_file: str):
        """
        Initialize the detector manager.

        Args:
            config_path (str): Path to the configuration file.
        """
        super().__init__(config_file)
        self.network_parser = NetworkParser(self.net_file, self.logger)

    # /usr/share/sumo/tools/output/generateTLSE1Detectors.py

    def generate_induction_loops(self):
        """
        Generate induction loops for the network.
        """
        output_file = os.path.join(self.network_outputs, "e1_detectors.add.xml")
        results_file = os.path.join(self.simulation_outputs, "e1output.xml")

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
        
    def generate_lanearea_detectors(self):
        """
        Generate lanearea detectors for the network.
        """
        output_file = os.path.join(self.network_outputs, "initial_e2_detectors.add.xml")
        results_file = os.path.join(self.simulation_outputs, "e2output.xml")
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
        
    def generate_multi_entry_exit_detectors(self):
        """
        Generate multi-entry/multi-exit detectors for the network.
        """
        output_file = os.path.join(self.network_outputs, "e3_detectors.add.xml")
        results_file = os.path.join(self.simulation_outputs, "e3output.xml")
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

    def get_lane_length(self, lane_id):
        """
        Get the length of a lane.

        Args:
            lane_id (str): Lane ID.

        Returns:
            float: Length of the lane.
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


    def modify_detectors(self):
        file_path = os.path.join(self.network_outputs, "initial_e2_detectors.add.xml")
        output_path = os.path.join(self.network_outputs, "e2_detectors.add.xml")



        tree = ET.parse(file_path)
        root = tree.getroot()

        for detector in root.findall('.//laneAreaDetector'):
            # Set the initial position of the detector (0.1 meters from the start of the lane)
            detector.set('pos', '0.1')

            # Get lane length (assuming this is retrieved or known elsewhere in the code)
            lane_id = detector.get('lane')
            lane_length = self.get_lane_length(lane_id)  # Implement this function to fetch lane lengths

            # Calculate maximum detector length based on the lane length
            pos = float(detector.get('pos'))
            max_length = round((lane_length - pos), 2)
            adjusted_length = max_length - 1.0  # Leave a 1 meter buffer
            # Set a safe detector length (slightly less than the max length)
            # adjusted_length = min(float(detector.get('length')), max_length) - 1.0  # Leave a 1 meter buffer

            # Cap the adjusted length if needed
            if adjusted_length > 200:
                adjusted_length = 200  # Cap the length at 200 meters

            detector.set('length', str(adjusted_length))

            # Ensure friendlyPos is set to 'true' for better error handling
            detector.set('friendlyPos', 'true')

        tree.write(output_path, encoding='utf-8', xml_declaration=True)


    def _get_junction_ids(self):
        """
        Get the junction IDs from the node_junction_mapping file.

        Returns:
            str: Comma-separated string of junction IDs.
        """
        node_junction_mapping_file = os.path.join(self.processing_outputs, 'node_junction_mapping.csv')
        node_junction_mapping = pd.read_csv(node_junction_mapping_file)
        junction_ids = node_junction_mapping['junction_id'].unique()
        junction_ids = ','.join(map(str, junction_ids))
        return junction_ids


    def execute_detector_generation(self):
        """
        Prepate the commands to generate detectors and execute them.
        """
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
        

        
if __name__ == "__main__":
    detector_generator = DetectorGenerator('configurations/main_config.yaml')
    detector_generator.execute_detector_generation()


