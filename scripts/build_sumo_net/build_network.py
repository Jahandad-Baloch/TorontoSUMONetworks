import os
import pandas as pd
from scripts.common.centreline_processor import CentrelineProcessor
from scripts.common.edge_types_xml import EdgeTypesXML
from scripts.common.network_base import NetworkBase

"""
This script builds a SUMO network by processing centreline data and traffic signal information.
path: scripts/build_sumo_net/build_network.py
"""

class SUMONetworkBuilder(NetworkBase):
    def __init__(self, config_file: str):
        """
        Initializes the SUMONetworkBuilder object.

        Args:
            config_path (str): Path to the configuration file.
        """
        super().__init__(config_file)
        self.prepare_directories()


    def network_setup(self):
        """
        Builds the SUMO network by setting up the network and processing the centreline data.
        """
        # Setting up network and processing centreline data       

        self.network_paths = {
            'net_file': os.path.join(self.network_outputs, f"{self.network_name}_{self.network_type}.net.xml"),
            'edge_types_file': os.path.join(self.network_outputs, f"{self.network_name}_edge_types.typ.xml"),
            'shapefile_prefix': os.path.join(self.shapefile_outputs, self.network_name)
        }
        self.geojson_file = self.get_geojson_path()
        self.tls_ids = self.get_tls_ids()
        self.process_network()
        self.save_edge_types()

    def get_geojson_path(self):
        """
        Locates and returns the path to the geojson file.

        Returns:
            str: Path to the geojson file.
        """
        centreline_dir = os.path.join(self.paths['raw_data'], 'toronto-centreline-tcl')
        for file in os.listdir(centreline_dir):
            if file.endswith('4326.geojson'):
                return os.path.join(centreline_dir, file)
        self.logger.error("GeoJSON file not found.")
        return None

    def get_tls_ids(self):
        """
        Extracts traffic signal IDs from the traffic signal locations file.

        Returns:
            str: Comma-separated string of traffic signal IDs.
        """
        tls_locations_dir = os.path.join(self.paths['raw_data'], 'traffic-signals-tabular')
        for file in os.listdir(tls_locations_dir):
            if 'Signal' in file and '4326.csv' in file:
                tls_file = os.path.join(tls_locations_dir, file)
                traffic_signals = pd.read_csv(tls_file)
                junction_ids = [int(jid) for jid in traffic_signals['NODE_ID'].tolist() if not pd.isna(jid)]
                tls_ids = ','.join(map(str, junction_ids))
                self.logger.info(f"Number of traffic signal IDs: {len(junction_ids)}")
                return tls_ids
        self.logger.error("Traffic signal IDs file not found.")
        return None

    def process_network(self):
        """
        Processes and builds the network using the centreline data.
        """
        self.logger.info(f"Processing {self.network_name} network.")
        
        # Process the centreline data
        processor = CentrelineProcessor(self.config, self.geojson_file, EdgeTypesXML.type_mappings, self.logger)
        processed_gdf = processor.process()
        
        if processed_gdf is not None:
            shapefile_path = f"{self.network_paths['shapefile_prefix']}.shp"
            processor.save_shapefile(processed_gdf, shapefile_path)
            self.logger.info(f"Processed centreline data and saved to {shapefile_path}")
            

    def save_edge_types(self):
        """
        Generates and saves the edge types XML file.
        """
        edge_types_xml = EdgeTypesXML.create(EdgeTypesXML.type_mappings)
        EdgeTypesXML.save(edge_types_xml, self.network_paths['edge_types_file'])
        self.logger.info(f"Saved edge types to {self.network_paths['edge_types_file']}")

    def get_netconvert_command(self):
        """
        Runs the netconvert command to convert the shapefile to a SUMO network file.
        """
        command = [
            "netconvert",
            "--output-file", self.network_paths['net_file'],
            "--shapefile-prefix", self.network_paths['shapefile_prefix'],
            "--tls.set", self.tls_ids,
            "--type-files", self.network_paths['edge_types_file'],
            "--shapefile.street-id", "LINK_ID",
            "--shapefile.name", "ST_NAME",
            "--shapefile.from-id", "REF_IN_ID",
            "--shapefile.to-id", "NREF_IN_ID",
            "--shapefile.type-id", "FUNC_CLASS",
            "--shapefile.laneNumber", "nolanes",
            "--shapefile.speed", "speed",
            "--remove-edges.isolated",
            "--geometry.min-radius.fix",
            "--no-turnarounds.tls",
            "--tls.rebuild"
        ]
        
        return command

    def build_network(self):
        """
        Builds the SUMO network by running the netconvert command.
        """
        # Load specific settings for processing
        self.network_setup()

        self.logger.info(f"Building {self.network_name} network.")
        command = self.get_netconvert_command()

        # self.logger.info(f"Executing command: {' '.join(command) if isinstance(command, list) else command}")

        self.executor.run_command(command)
        self.logger.info(f"SUMO network built successfully.")
        self.logger.info(f"\n.......................\n")

if __name__ == "__main__":
    builder = SUMONetworkBuilder('configurations/main_config.yaml')
    builder.build_network()
