import numpy as np
import pandas as pd
from pyproj import Transformer, CRS

class CoordinateTransformer:
    def __init__(self, proj_parameter: str, net_offset_x: float, net_offset_y: float):
        self.transformer = Transformer.from_proj(CRS.from_proj4(proj_parameter), CRS.from_epsg(4326), always_xy=True)
        self.net_offset_x = net_offset_x
        self.net_offset_y = net_offset_y

    def transform_to_geojson(self, x: float, y: float) -> tuple:
        lon, lat = self.transformer.transform(x - self.net_offset_x, y - self.net_offset_y)
        return lon, lat


class JunctionMatcher:
    def __init__(self, junctions: dict, transformer: CoordinateTransformer, traffic_settings, logger):
        self.junctions = junctions
        self.transformer = transformer
        self.threshold = traffic_settings['threshold_value']
        self.logger = logger

    def find_nearest_junction(self, df: pd.DataFrame):
        results_found = {}
        results_not_found = {}

        junction_coords = np.array([
            self.transformer.transform_to_geojson(data['x'], data['y'])
            for data in self.junctions.values()
        ])
        junction_ids = list(self.junctions.keys())

        for _, row in df.iterrows():
            node_id = int(row['centreline_id'])
            lon, lat = row['lng'], row['lat']

            distances = np.sqrt((junction_coords[:, 0] - lon) ** 2 + (junction_coords[:, 1] - lat) ** 2)
            closest_distance = np.min(distances)
            closest_junction_id = junction_ids[np.argmin(distances)]

            if closest_distance <= self.threshold:
                results_found[node_id] = {'junction_id': int(closest_junction_id), 'distance': round(closest_distance, 4)}
            else:
                results_not_found[node_id] = {'junction_id': None, 'distance': None}

        node_junction_mapping_df = pd.DataFrame.from_dict(results_found, orient='index').reset_index()
        node_junction_mapping_df.columns = ['centreline_id', 'junction_id', 'distance']

        self.logger.info(f"Nodes matched to junctions: {len(results_found)}")
        return node_junction_mapping_df

    def get_inc_edges(self, node_junction_mapping_df, edge_directions):
        """Get incoming edges for each junction and assign directions from self.edge_directions."""
        
        junction_ids = node_junction_mapping_df['junction_id'].unique()
        junction_ids = list(map(str, junction_ids))
        
        junctions_with_directions = {}
        for junction_id in junction_ids:
            if junction_id in self.junctions:
                inc_lanes = self.junctions[junction_id]['incLanes']
                incoming_edge_ids = set(inc_lane.split('_')[0] for inc_lane in inc_lanes)
                junctions_with_directions[junction_id] = {'edge_ids': '|'.join(incoming_edge_ids), 'directions': '|'.join([edge_directions.get(edge_id, 'Unknown') for edge_id in incoming_edge_ids])}
        
        junctions_with_directions_df = pd.DataFrame.from_dict(junctions_with_directions, orient='index').reset_index()
        junctions_with_directions_df.columns = ['junction_id', 'edge_ids', 'directions']

        self.logger.info(f"Junctions with directions: {len(junctions_with_directions)}")
        return junctions_with_directions_df
