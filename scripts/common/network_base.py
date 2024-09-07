import os
from scripts.common.utils import ConfigLoader, LoggerSetup, FileIO
from scripts.common.command_executor import CommandExecutor

"""
This script contains the base class for network
path: scripts/common/network_base.py
"""

class NetworkBase:
    def __init__(self, config_path):
        """
        Initialize the base network settings.

        Args:
            config_path (str): Path to the configuration file.
        """
        self.config = ConfigLoader.load_config(config_path)
        self.logger = LoggerSetup.setup_logger(self.__class__.__name__.lower(), self.config['logging']['log_dir'], self.config['logging']['log_level'])
        self.executor = CommandExecutor(logger=self.logger)
        self.sumo_tools_path = self.executor.get_sumo_tools_path()
        self._set_network_settings()

    def _set_network_settings(self):
        """
        Set the network settings based on the network extent specified in the execution settings.
        """
        self.paths = self.config['paths']
        network_extent = self.config['execution_settings']['network_extent']
        self.network_settings = self.config['network_settings'].get(network_extent)
        self.routing_settings = self.config['routing_settings']
        self.simulation_settings = self.config['simulation_settings']
        self.analysis_settings = self.config['analysis_settings']
        self.traffic_settings = self.config['traffic_settings']
        self.detector_settings = self.config['detector_settings']
        self.fetch_data_settings = self.config['transportation_datasets']
        self.network_area = self.network_settings['network_area']
        self.network_name = self.network_area.replace(' ', '_').lower()
        self.network_type = self.network_settings['network_type']
        self.net_file = os.path.join(self.paths['network_data'], self.network_name, f"{self.network_name}_{self.network_type}.net.xml")
        self.traffic_volume_file = os.path.join(self.paths['traffic_volume_dir'], self.traffic_settings['traffic_volume_file'])
        self.network_outputs = os.path.join(self.paths['network_data'], self.network_name)
        self.processing_outputs = os.path.join(self.paths['processed_data'], self.network_name)
        self.simulation_outputs = os.path.join(self.paths['simulation_data'], self.network_name)
        self.shapefile_outputs = os.path.join(self.paths['network_data'], self.network_name, 'arcview')
        self.sumo_cfg_file = os.path.join(self.network_outputs, f"{self.network_name}_sumo_config.sumocfg")


    def prepare_directories(self):
        """
        Ensure that necessary directories exist.
        """
        os.makedirs(self.network_outputs, exist_ok=True)
        os.makedirs(self.processing_outputs, exist_ok=True)
        os.makedirs(self.simulation_outputs, exist_ok=True)
        os.makedirs(self.shapefile_outputs, exist_ok=True)