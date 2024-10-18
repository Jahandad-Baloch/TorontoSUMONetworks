import os
import pandas as pd
from scripts.common.edge_types_xml import EdgeTypesXML
from scripts.common.network_base import NetworkBase
from scripts.common.centreline_processor import CentrelineProcessor

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
        self.centreline_processor = CentrelineProcessor(config_file)

    def get_tls_ids(self, junction_ids):
        """
        Extracts traffic signal IDs from the traffic signal locations file.

        Returns:
            str: Comma-separated string of traffic signal IDs.
        """
        for file in os.listdir(self.tls_locations_dir):
            if 'Signal' in file and '4326.csv' in file:
                tls_file = os.path.join(self.tls_locations_dir, file)
                tls_df = pd.read_csv(tls_file)
                node_ids = tls_df['NODE_ID'].tolist()

                # Convert to int and remove 'nan' values
                node_ids = [int(nid) for nid in node_ids if not pd.isna(nid)]
                filtered_node_ids = [nid for nid in node_ids if nid in junction_ids]

                tls_ids = ','.join(map(str, filtered_node_ids))
                self.logger.info(f"Found {len(filtered_node_ids)} traffic signals in the network.")
                return tls_ids
        return None

    def get_netconvert_command(self):
        command = [
            "netconvert",
            "--output-file", self.net_file,
            "--shapefile-prefix", self.shapefile_prefix,
            "--tls.set", self.tls_ids,
            "--type-files", self.edge_types_file,
            "--shapefile.street-id", "LINK_ID",
            "--shapefile.name", "ST_NAME",
            "--shapefile.from-id", "REF_IN_ID",
            "--shapefile.to-id", "NREF_IN_ID",
            "--shapefile.type-id", "FUNC_CLASS",
            "--shapefile.laneNumber", "nolanes",
            "--shapefile.speed", "speed",
            # "--sidewalks.guess", "true",
            # "--sidewalks.guess.max-speed", "6",
            # "--sidewalks.guess.from-permissions", "true",
            # "--bikelanes.guess", "true",
            # "--bikelanes.guess.max-speed", "6",
            # "--bikelanes.guess.from-permissions", "true",
            "--remove-edges.isolated",
            "--geometry.min-radius.fix",
            # "--geometry.min-radius", "9",  # Set minimum radius for geometry
            # "--junctions.corner-detail", "1",  # Smaller value for more realistic internal edges
            "--no-internal-links", "true",
            "--no-turnarounds",
            "--tls.rebuild"
        ]

        return command


    def build_network(self):
        """
        Builds the SUMO network by running the netconvert command.
        """
        # Load specific settings for processing
        active_types = EdgeTypesXML.create(self.network_type, self.edge_types_file)
        self.centreline_processor.filter_centreline_data(active_types)
        self.tls_ids = self.get_tls_ids(self.centreline_processor.junction_ids)

        self.logger.info(f"Building {self.network_name} network.")
        command = self.get_netconvert_command()

        # self.logger.info(f"Executing command: {' '.join(command) if isinstance(command, list) else command}")

        self.executor.run_command(command)
        self.logger.info(f"SUMO network built successfully.")
        self.logger.info(f"\n.......................\n")

if __name__ == "__main__":
    builder = SUMONetworkBuilder('configurations/main_config.yaml')
    builder.build_network()
