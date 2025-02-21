import numpy as np
import pandas as pd

""" 
Description: This script contains the classes for matching nodes to junctions and getting incoming edges for each junction.
path: scripts/traffic_data_processing/junction_matcher.py
"""

class JunctionMatcher:
    """Matches network nodes to junctions and retrieves incoming edges.

    Args:
        network_parser: Parsed network object.
        traffic_settings (dict): Traffic settings (expects key 'threshold_value').
        logger: Logger instance.
    """
    def __init__(self, network_parser, traffic_settings: dict, logger) -> None:
        self.network_parser = network_parser
        self.net = network_parser.net
        self.threshold: float = traffic_settings['threshold_value']
        self.logger = logger

    def find_nearest_junction(self, df: pd.DataFrame) -> pd.DataFrame:
        """Find the nearest junctions for each network node.

        Args:
            df (pd.DataFrame): DataFrame containing node data.
            
        Returns:
            pd.DataFrame: Mapping of centreline_id to junction_id with distance.
        """
        results_found = []
        results_not_found = []

        # Using sumolib to get junction coordinates
        junctions = {junction.getID(): junction for junction in self.net.getNodes() if not junction.getInternal()}
        junction_coords = np.array([
            self.network_parser.transform_to_geojson(junction.getCoord()[0], junction.getCoord()[1])
            for junction in junctions.values()
        ])
        junction_ids = list(junctions.keys())

        for _, row in df.iterrows():
            node_id = int(row['centreline_id'])
            lon, lat = row['lng'], row['lat']

            distances = np.sqrt((junction_coords[:, 0] - lon) ** 2 + (junction_coords[:, 1] - lat) ** 2)
            closest_distance = np.min(distances)
            closest_junction_id = junction_ids[np.argmin(distances)]

            if closest_distance <= self.threshold:
                results_found.append({
                    'centreline_id': node_id,
                    'junction_id': closest_junction_id,
                    'distance': round(closest_distance, 4)
                })
            else:
                results_not_found.append({
                    'centreline_id': node_id,
                    'junction_id': None,
                    'distance': None
                })

        # Convert to DataFrame with 3 columns
        node_junction_mapping_df = pd.DataFrame(results_found, columns=['centreline_id', 'junction_id', 'distance'])

        self.logger.info(f"Nodes matched to junctions: {len(results_found)}")
        return node_junction_mapping_df

    def get_inc_edges(self, node_junction_mapping_df: pd.DataFrame, edge_directions: dict) -> pd.DataFrame:
        """Retrieve incoming edges for each junction with assigned directions.

        Args:
            node_junction_mapping_df (pd.DataFrame): Mapping of nodes to junctions.
            edge_directions (dict): Mapping of edge IDs to directions.
            
        Returns:
            pd.DataFrame: DataFrame with junction_id, edge_ids, and directions.
        """
        junction_ids = node_junction_mapping_df['junction_id'].unique().tolist()
        junctions_with_directions = {}
        for junction_id in map(str, junction_ids):
            junction = self.net.getNode(junction_id)
            if junction:
                inc_edges = {edge.getID() for edge in junction.getIncoming()}
                directions = '|'.join([edge_directions.get(edge, 'Unknown') for edge in inc_edges])
                junctions_with_directions[junction_id] = {'edge_ids': '|'.join(inc_edges), 'directions': directions}
        junctions_with_directions_df = pd.DataFrame.from_dict(junctions_with_directions, orient='index').reset_index()
        junctions_with_directions_df.columns = ['junction_id', 'edge_ids', 'directions']
        self.logger.info(f"Junctions with directions: {len(junctions_with_directions)}")
        return junctions_with_directions_df
