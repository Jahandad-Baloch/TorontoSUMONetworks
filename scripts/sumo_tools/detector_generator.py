import os
import pandas as pd
from scripts.common.network_base import NetworkBase
from scripts.common.utils import XMLFile


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
        self.prepare_directories()

    # /usr/share/sumo/tools/output/generateTLSE1Detectors.py

    def generate_induction_loops(self):
        """
        Generate induction loops for the network.
        """
        output_file = os.path.join(self.network_outputs, "e1_detectors.add.xml")
        results_file = os.path.join(self.simulation_outputs, "e1output.xml")

        # Generate XML file
        XMLFile.create_xml_file("additional", output_file)

        distance = self.detector_settings['induction_loop_detectors']['distance']
        frequency = self.detector_settings['induction_loop_detectors']['frequency']
        tool_e1 = os.path.join(self.sumo_tools_path, "output", "generateTLSE1Detectors.py")

        command = [
            "python", tool_e1,
            "-n", self.net_file,
            "-d", str(distance),
            "-f", str(frequency),
            "-o", output_file,
            "-r", "e1output.xml"
        ]
        self.executor.run_command(command)
        
    def generate_lanearea_detectors(self):
        """
        Generate lanearea detectors for the network.
        """
        output_file = os.path.join(self.network_outputs, "e2_detectors.add.xml")
        results_file = os.path.join(self.simulation_outputs, "e2output.xml")
        XMLFile.create_xml_file(results_file, "additional")

        detector_length = self.detector_settings['lanearea_detectors']['detector_length']
        distance = self.detector_settings['lanearea_detectors']['distance']
        frequency = self.detector_settings['lanearea_detectors']['frequency']
        tool_e2 = os.path.join(self.sumo_tools_path, "output", "generateTLSE2Detectors.py")

        command = [
            "python", tool_e2,
            "-n", self.net_file,
            "-d", str(distance),
            "-l", str(detector_length),
            "-f", str(frequency),
            "-o", output_file,
            "-r", "e2output.xml"
        ]
        
        if self.detector_settings['lanearea_detectors']['tl_coupled']:
            command.append("--tl-coupled")
        
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
        junction_ids = self._get_junction_ids()
        tool_e3 = os.path.join(self.sumo_tools_path, "output", "generateTLSE3Detectors.py")


        command = [
            "python", tool_e3,
            "-n", self.net_file,
            "-j", junction_ids,
            "-d", str(distance),
            "-f", str(frequency),
            "--min-pos", str(min_position),
            "-o", output_file,
            "-r", "e3output.xml"
        ]
        
        if self.detector_settings['multi_entry_exit_detectors']['joined']:
            command.append("--joined")
        if self.detector_settings['multi_entry_exit_detectors']['interior']:
            command.append("--interior")
        if self.detector_settings['multi_entry_exit_detectors']['follow_turnaround']:
            command.append("--follow-turnaround")
        
        self.executor.run_command(command)

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
        if self.detector_settings['generate_induction_loops']:
            self.logger.info("Generating induction loops...")
            self.generate_induction_loops()
            self.logger.info("End of induction loop generation process.")
        
        if self.detector_settings['generate_lanearea_detectors']:
            self.logger.info("Generating lanearea detectors...")
            self.generate_lanearea_detectors()
            self.logger.info("End of lanearea detector generation process.")
            
        if self.detector_settings['generate_multi_entry_exit_detectors']:
            self.logger.info("Generating multi-entry/multi-exit detectors...")
            self.generate_multi_entry_exit_detectors()
            self.logger.info("End of multi-entry/multi-exit detector generation process.")
        
        self.logger.info("Detector Generation Completed.")
        self.logger.info(f"\n.......................\n")
        

        
if __name__ == "__main__":
    detector_generator = DetectorGenerator('configurations/main_config.yaml')
    detector_generator.execute_detector_generation()


