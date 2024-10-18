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
        self._set_network_settings()

    def _set_network_settings(self):
        """
        Set the network settings based on the network extent specified in the execution settings.
        """
        # Ensure that the SUMO_HOME environment variable is set.
        sumo_home = os.environ.get('SUMO_HOME')
        if sumo_home is None:
            raise EnvironmentError("SUMO_HOME environment variable not set.")

        # path to the SUMO tools directory
        self.sumo_tools_path = os.path.join(sumo_home, 'tools')

        # network settings specified in the execution settings.
        self.paths = self.config['paths']
        self.network_extent = self.config['network_settings']['network_extent']
        self.network_settings = self.config['network_settings'].get(self.network_extent)
        self.routing_settings = self.config['routing_settings']
        self.simulation_settings = self.config['simulation_settings']
        self.analysis_settings = self.config['analysis_settings']
        self.traffic_settings = self.config['traffic_settings']
        self.detector_settings = self.config['detector_settings']
        self.fetch_data_settings = self.config['transportation_datasets']

        # network settings
        self.network_area = self.network_settings['network_area']
        self.network_name = self.network_area.replace(' ', '_').lower()
        self.network_type = self.network_settings['network_type']

        # Paths for the network data
        self.net_file = os.path.join(self.paths['network_data'], self.network_name, f"{self.network_name}_{self.network_type}.net.xml")
        self.network_outputs = os.path.join(self.paths['network_data'], self.network_name)
        self.sumo_cfg_file = os.path.join(self.network_outputs, f"{self.network_name}_sumo_config.sumocfg")
        self.edge_types_file = os.path.join(self.network_outputs, f"{self.network_name}_edge_types.typ.xml")
        self.shapefile_outputs = os.path.join(self.paths['network_data'], self.network_name, 'arcview')
        self.shapefile_prefix = os.path.join(self.shapefile_outputs, self.network_name)
        self.shapefile_path = f"{self.shapefile_prefix}.shp"



        # Paths for the traffic data processing outputs
        self.traffic_volume_file = os.path.join(self.paths['traffic_volume_dir'], self.traffic_settings['traffic_volume_file'])
        self.processing_outputs = os.path.join(self.paths['processed_data'], self.network_name)
        self.edge_directions_path = os.path.join(self.processing_outputs, f'edge_directions.csv')
        self.node_junction_mapping_path = os.path.join(self.processing_outputs, f'node_junction_mapping.csv')
        self.junction_directions_path = os.path.join(self.processing_outputs, f'junction_directions.csv')

        self.simulation_outputs = os.path.join(self.paths['simulation_data'], self.network_name)

        # Paths for the routes outputs
        self.modes = self.traffic_settings['active_modes']
        self.files_by_mode = {}
        for mode in self.modes:
            mode_files = {
                'edge_types_file': os.path.join(self.network_outputs, f"{self.network_name}_{mode}_edge_types.typ.xml"),
                'vtype_output_file': os.path.join(self.network_outputs, f"{self.network_name}_{mode}_vtype.rou.xml"),
                'output_route_file': os.path.join(self.network_outputs, f"{self.network_name}_{mode}_routes.rou.xml"),
                'output_trips_file': os.path.join(self.processing_outputs, f"{self.network_name}_{mode}.trips.xml"),
                'initial_route_file': os.path.join(self.processing_outputs, f"initial_route_file_{mode}.rou.xml"),
                'turn_counts_file': os.path.join(self.processing_outputs, f"turning_movements_{mode}.xml")
            }
            self.files_by_mode[mode] = mode_files

        # GTFS import settings
        self.bus_routes_file = os.path.join(self.network_outputs, f"{self.network_name}_public_transport.rou.xml")
        self.bus_vtype_file = os.path.join(self.network_outputs, f"{self.network_name}_public_transport_vtype.rou.xml")
        self.bus_routes_additional = os.path.join(self.network_outputs, f"{self.network_name}_gtfs_stops_routes.add.xml")

        # paths to the raw data
        centreline_dir = os.path.join(self.paths['raw_data'], 'toronto-centreline-tcl')
        for file in os.listdir(centreline_dir):
            if file.endswith('4326.geojson'):
                self.geojson_file = os.path.join(centreline_dir, file)

        self.gtfs_file = os.path.join(self.paths['raw_data'], 'ttc-routes-and-schedules', [f for f in os.listdir(os.path.join(self.paths['raw_data'], 'ttc-routes-and-schedules')) if f.endswith('.zip')][0])
        self.tls_locations_dir = os.path.join(self.paths['raw_data'], 'traffic-signals-tabular')

        if self.network_extent == 'by_ward_name':
            boundaries_dir = os.path.join(self.paths['raw_data'], 'city-wards')
        elif self.network_extent == 'by_neighbourhood' or 'by_neighborhood':
            boundaries_dir = os.path.join(self.paths['raw_data'], 'neighbourhoods')
        
        for file in os.listdir(boundaries_dir):
            if file.endswith('4326.geojson'):
                self.bounderies_file = os.path.join(boundaries_dir, file)
                
        # Ensure that necessary directories exist.
        os.makedirs(self.network_outputs, exist_ok=True)
        os.makedirs(self.processing_outputs, exist_ok=True)
        os.makedirs(self.simulation_outputs, exist_ok=True)
        os.makedirs(self.shapefile_outputs, exist_ok=True)
        os.makedirs(self.shapefile_outputs, exist_ok=True)