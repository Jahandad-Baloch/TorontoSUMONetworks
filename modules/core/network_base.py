# modules/network/network_base.py
import os
from pathlib import Path
from modules.common.command_executor import CommandExecutor
from modules.core.app_context import AppContext

class NetworkBase:
    """
    Base class for network operations that provides shared network settings and utility methods.

    Attributes:
        app_context (:obj:`AppContext`): Shared application context.
        config (dict): Shortcut to configuration settings.
        logger (logging.Logger): Logger instance.
        executor (:obj:`CommandExecutor`): Utility to run shell commands.
    """
    def __init__(self, app_context: AppContext) -> None:
        """
        Initializes the network settings using the provided AppContext.

        Args:
            app_context (:obj:`AppContext`): The central application context.
        """
        self.app_context = app_context
        self.config = app_context.config
        self.logger = app_context.logger
        self.executor = CommandExecutor(logger=self.logger)
        self._set_network_settings()

    def _set_network_settings(self) -> None:
        """
        Sets network settings and paths based on the configuration.

        Raises:
            EnvironmentError: If the SUMO_HOME environment variable is not set.
        """
        sumo_home = os.environ.get('SUMO_HOME')
        if not sumo_home:
            raise EnvironmentError("SUMO_HOME environment variable not set.")

        # Updated network settings from configuration.
        # Replace old key 'network_settings' with new key 'network'
        net_settings = self.config['network']
        self.network_extent = net_settings['extent']
        self.network_type = net_settings['type']
        self.network_area = net_settings['area'].get(self.network_extent, 'default_area')
        self.network_name = self.network_area.replace(' ', '_').lower()

        # Use pathlib for path handling.
        self.paths = {key: Path(val) for key, val in self.config['paths'].items()}
        self.network_outputs = self.paths['network_data'] / self.network_name
        self.net_file = self.network_outputs / f"{self.network_name}_{self.network_type}.net.xml"
        self.sumo_cfg_file = self.network_outputs / f"{self.network_name}_sumo_config.sumocfg"
        self.edge_types_file = self.network_outputs / f"{self.network_name}_edge_types.typ.xml"
        self.shapefile_prefix = self.network_outputs / self.network_name
        self.shapefile_path = self.shapefile_prefix.with_suffix('.shp')

        # Create necessary directories.
        for path in [self.network_outputs, self.paths['processed_data'], self.paths['simulation_data']]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Store simulation settings.
        self.routing_settings = self.config['routing_settings']
        self.simulation_settings = self.config['simulation_settings']
        self.analysis_settings = self.config['analysis_settings']
        self.traffic_settings = self.config['traffic_settings']
        self.detector_settings = self.config['detector_settings']
        self.data_acquisition_settings = self.config['transportation_datasets']

        # Paths for the network data
        self.sumo_tools_path = os.path.join(sumo_home, 'tools')
        self.paths = self.config['paths']
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

                
        # Ensure that necessary directories exist.
        os.makedirs(self.network_outputs, exist_ok=True)
        os.makedirs(self.processing_outputs, exist_ok=True)
        os.makedirs(self.simulation_outputs, exist_ok=True)
        os.makedirs(self.shapefile_outputs, exist_ok=True)
        os.makedirs(self.shapefile_outputs, exist_ok=True)

