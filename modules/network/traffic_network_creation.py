# modules/network/traffic_network_builder.py
import os
import pandas as pd
from modules.core.simulation_task import SimulationTask
from modules.common.edge_types_xml import EdgeTypesXML
from modules.network.centreline_processor import CentrelineProcessor
from modules.common.command_executor import CommandExecutor

class TrafficNetworkCreation(SimulationTask):
    """
    Creates the SUMO network by processing centreline data and traffic signal information.

    This task generates edge types, processes centreline data to create a shapefile, extracts
    traffic light IDs and then invokes the netconvert command to build the network.

    Attributes:
        app_context (:obj:`AppContext`): The application context containing configuration and logger.
    """
    
    def __init__(self, app_context):
        """
        Initializes the TrafficNetworkCreationTask.

        Args:
            app_context (:obj:`AppContext`): Shared application context.
        """
        super().__init__(app_context)
        self.app_context = app_context
        # Initialize centreline processor for processing geojson data.
        self.centreline_processor = CentrelineProcessor(
            self.app_context.config['paths']['centreline_geojson'], 
            self.app_context.logger
        )
        # Set up network-related properties from configuration.
        self.paths = self.app_context.config['paths']
        # Updated network configuration reading
        network_config = self.app_context.config['network']
        self.network_extent = network_config['extent']
        self.network_type = network_config['type']
        if self.network_extent == 'by_junctions':
            self.network_name = network_config['area'][self.network_extent]['name'].replace(' ', '_').lower()
            self.junction_ids_config = network_config['area'][self.network_extent]['junction_ids']
        else:
            self.network_name = network_config['area'][self.network_extent].replace(' ', '_').lower()
            self.junction_ids_config = None

        self.network_outputs = os.path.join(self.paths['network_data'], self.network_name)
        self.net_file = os.path.join(self.network_outputs, f"{self.network_name}_{self.network_type}.net.xml")
        self.shapefile_prefix = os.path.join(self.network_outputs, self.network_name)
        self.shapefile_path = f"{self.shapefile_prefix}.shp"
        self.edge_types_file = os.path.join(self.network_outputs, f"{self.network_name}_edge_types.typ.xml")
        self.tls_locations_dir = os.path.join(self.paths['raw_data'], 'traffic-signals-tabular')

        # Initialize command executor.
        self.executor = CommandExecutor(logger=self.app_context.logger)
        self.tls_ids = ""

    def execute(self):
        """
        Executes the task to build the SUMO network.

        Steps:
          1. Create edge types XML.
          2. Process centreline data to produce a shapefile.
          3. Extract traffic signal IDs.
          4. Build and execute the netconvert command.
        """
        # 1. Generate edge types XML.
        active_types = EdgeTypesXML.create(self.network_type, self.edge_types_file)
        # 2. Process centreline data.
        self.centreline_processor.filter_centreline_data(
            active_types, 
            self.network_name, 
            self.network_extent, 
            self.paths, 
            self.shapefile_path, 
            junction_ids=self.junction_ids_config
        )
        # 3. Get the traffic signal IDs.
        self.tls_ids = self.get_tls_ids(self.centreline_processor.junction_ids)

        # 4. Build and run netconvert command.
        command = self.get_netconvert_command()
        self.app_context.logger.info(f"Executing command: {' '.join(command)}")
        self.executor.run_command(command)
        self.app_context.logger.info("SUMO network built successfully.")

    def get_tls_ids(self, junction_ids):
        """
        Extracts traffic signal IDs from CSV files in the TLS directory.

        Args:
            junction_ids (list): List of junction IDs to filter against.

        Returns:
            str: Comma-separated traffic signal IDs.
        """

        try:
            for file in os.listdir(self.tls_locations_dir):
                if 'Signal' in file and '4326.csv' in file:
                    self.logger.info(f"Reading TLS file: {file}")
                    tls_file = os.path.join(self.tls_locations_dir, file)
                    tls_df = pd.read_csv(tls_file)
                    node_ids = [int(nid) for nid in tls_df['NODE_ID'].tolist() if pd.notna(nid)]
                    self.logger.info(f"Found {len(node_ids)} total nodes in the TLS file.")
                    self.logger.info(f"Found {len(junction_ids)} total junctions in the network.")

                    filtered_ids = [nid for nid in node_ids if nid in junction_ids]
                    self.app_context.logger.info(f"Found {len(filtered_ids)} traffic signals in the network.")
                    return ','.join(map(str, filtered_ids))
        except Exception as e:
            self.app_context.logger.error(f"Error reading TLS file: {e}")
        return ""

    def get_netconvert_command(self):
        """
        Constructs the netconvert command list.

        Returns:
            list: Arguments for netconvert.
        """
        command = [
            "netconvert",
            "--output-file", self.net_file,
            "--shapefile-prefix", self.shapefile_prefix,
            "--tls.set", self.tls_ids if self.tls_ids else "",
            "--type-files", self.edge_types_file,
            "--shapefile.street-id", "LINK_ID",
            "--shapefile.name", "ST_NAME",
            "--shapefile.from-id", "REF_IN_ID",
            "--shapefile.to-id", "NREF_IN_ID",
            "--shapefile.type-id", "FUNC_CLASS",
            "--shapefile.laneNumber", "nolanes",
            "--shapefile.speed", "speed",
            "--remove-edges.isolated",
            "--geometry.min-radius.fix",
            "--no-turnarounds.except-turnlane", "true",
            "--tls.rebuild"
        ]
        return [arg for arg in command if arg]
