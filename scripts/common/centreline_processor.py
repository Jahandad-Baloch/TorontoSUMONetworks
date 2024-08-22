# scripts/build_sumo_net/centreline_processor.py
# This script processes the centreline data for building the SUMO network.

import os
import geopandas as gpd


class CentrelineProcessor:
    def __init__(self, configs, geojson_file, active_types, logger):
        """
        Initialize the CentrelineProcessor object.
        
        Args:
            geojson_file (str): Path to the GeoJSON file.
            active_types (dict): Mapping of active feature codes to attributes.
            logger (logging.Logger): Logger object for logging.
            build_subnetwork (bool): Flag to determine if processing for a subnetwork.
            network_settings (dict): Settings related to the network, includes subnetwork area definition.
        """
        self.geojson_file = geojson_file
        self.active_types = active_types
        self.logger = logger
        self.config = configs
        self._set_network_settings()

    def _set_network_settings(self):
        """
        Set the network settings based on the network extent specified in the execution settings.
        """
        self.paths = self.config['paths']
        network_extent = self.config['execution_settings']['network_extent']
        self.network_settings = self.config['network_settings'].get(network_extent)
        self.network_area = self.network_settings ['network_area']
        self.network_name = self.network_area.replace(' ', '_').lower()
        self.network_type = self.network_settings ['network_type']

        self.centreline_gdf = self.setup_processing(network_extent)

    def setup_processing(self, network_extent):
        """
        Setup and return the processed GeoDataFrame for the centreline data.
        """
        try:
            if network_extent == 'city_wide':
                self.logger.info(f"Processing city-wide centreline data for: {self.network_area}.")
                gdf = gpd.read_file(self.geojson_file)
                return gdf

            elif network_extent == 'by_ward_name':
                self.logger.info(f"Processing centreline data for ward: {self.network_area}")
                # network_area is the ward name
                gdf = gpd.read_file(self.geojson_file)
                ward_boundaries_file = self.get_boundaries_file(network_extent)
                boundaries_gdf = gpd.read_file(ward_boundaries_file)
                filtered_centreline_gdf = self.get_centreline_for_area(self.network_area, boundaries_gdf, gdf)
                return filtered_centreline_gdf

            elif network_extent == 'by_neighbourhood' or 'by_neighborhood':
                self.logger.info(f"Processing centreline data for neighbourhood: {self.network_area}")
                # network_area is the neighbourhood name
                gdf = gpd.read_file(self.geojson_file)
                boundaries_file = self.get_boundaries_file(network_extent)
                boundaries_gdf = gpd.read_file(boundaries_file)
                filtered_centreline_gdf = self.get_centreline_for_area(self.network_area, boundaries_gdf, gdf)
                return filtered_centreline_gdf

        except Exception as e:
            self.logger.error(f"Error in setup processing: {e}")
            return None

    def get_boundaries_file(self, network_extent):
        """
        Locates and returns the path to the geojson file.

        Returns:
            str: Path to the geojson file.
        """

        if network_extent == 'by_ward_name':
            boundaries_dir = os.path.join(self.paths['raw_data'], 'city-wards')
        elif network_extent == 'by_neighbourhood' or 'by_neighborhood':
            boundaries_dir = os.path.join(self.paths['raw_data'], 'neighbourhoods')
        else:
            self.logger.error("Invalid network extent.")
            return None
        
        for file in os.listdir(boundaries_dir):
            if file.endswith('4326.geojson'):
                return os.path.join(boundaries_dir, file)
        self.logger.error("Boundaries file not found.")
        return None

    def process(self):
        """
        Process the centreline data.
        Returns:
            geopandas.GeoDataFrame: Processed centreline data.
        """
        if self.centreline_gdf is None:
            self.logger.error("Failed to load or process the centreline GeoDataFrame.")
            return None

        self.logger.info("Processing centreline data.")
        processed_gdf = self.centreline_gdf[self.centreline_gdf['FEATURE_CODE'].isin(self.active_types.keys())]
        processed_gdf['nolanes'] = processed_gdf['FEATURE_CODE'].apply(lambda x: self.active_types[x]['numLanes'])
        processed_gdf['speed'] = processed_gdf['FEATURE_CODE'].apply(lambda x: self.active_types[x]['speed'])
        processed_gdf['DIR_TRAVEL'] = processed_gdf.apply(
            lambda row: 'B' if row['ONEWAY_DIR_CODE'] == 0 else ('F' if row['ONEWAY_DIR_CODE'] == 1 else 'T'), axis=1)
        processed_gdf.rename(columns={
            'CENTRELINE_ID': 'LINK_ID',
            'LINEAR_NAME_FULL_LEGAL': 'ST_NAME',
            'FROM_INTERSECTION_ID': 'REF_IN_ID',
            'TO_INTERSECTION_ID': 'NREF_IN_ID',
            'FEATURE_CODE': 'FUNC_CLASS',
        }, inplace=True)
        required_fields = ['LINK_ID', 'ST_NAME', 'REF_IN_ID', 'NREF_IN_ID', 'FUNC_CLASS', 'speed', 'nolanes', 'DIR_TRAVEL', 'geometry']
        return processed_gdf[required_fields]

    def get_centreline_for_area(self, area_name, boundaries_gdf, centreline_gdf):
        """
        Filter centreline data for a specific area.
        """
        try:
            area_polygon = boundaries_gdf[boundaries_gdf['AREA_NAME'] == area_name]['geometry'].values[0]
            centreline_for_area = centreline_gdf[centreline_gdf.intersects(area_polygon)]
            return centreline_for_area

        except Exception as e:
            self.logger.error(f"Error filtering centreline data for area {area_name}: {e}")
            return None

    def save_shapefile(self, gdf, output_path):
        """
        Save the GeoDataFrame to a shapefile.
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            gdf.to_file(output_path)
            self.logger.info(f"Shapefile saved successfully to {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to save shapefile: {e}")