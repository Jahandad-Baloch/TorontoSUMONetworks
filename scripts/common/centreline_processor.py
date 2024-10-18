# scripts/build_sumo_net/centreline_processor.py
# This script processes the centreline data for building the SUMO network.

import geopandas as gpd
from scripts.common.network_base import NetworkBase

class CentrelineProcessor(NetworkBase):
    def __init__(self, config_file: str):
        """
        Initialize the CentrelineProcessor object.

        Args:
            config_path (str): Path to the configuration file.
        """
        super().__init__(config_file)
        self.centreline_gdf = None
        self.junction_ids = []

    def filter_centreline_data(self, active_types):
        """
        Setup and return the processed GeoDataFrame for the centreline data.
        """
        try:
            gdf = gpd.read_file(self.geojson_file) 

            if self.network_extent == 'city_wide':
                self.logger.info(f"Processing city-wide centreline data for: {self.network_area}.")

                centreline_gdf = gdf

            elif self.network_extent == 'by_ward_name' or self.network_extent == 'by_neighbourhood' or self.network_extent == 'by_neighborhood':
                self.logger.info(f"Processing centreline data for: {self.network_area} {self.network_extent}.")

                boundaries_gdf = gpd.read_file(self.bounderies_file)
                bordered_centreline_gdf = self.get_centreline_for_area(self.network_area, boundaries_gdf, gdf)
                self.junction_ids = bordered_centreline_gdf['FROM_INTERSECTION_ID'].unique().tolist() + bordered_centreline_gdf['TO_INTERSECTION_ID'].unique().tolist()
                centreline_gdf = bordered_centreline_gdf

            elif self.network_extent == 'by_junctions':
                self.logger.info(f"Processing centreline data for specified junctions.")
                junction_ids = self.network_settings.get('junction_ids', [])
                if not self.network_settings['junction_ids']:
                    self.logger.error("No junction IDs provided for by_junctions network extent.")
                    return None

                # Filter the data based on the junction IDs
                filtered_centreline_gdf = gdf[gdf['FROM_INTERSECTION_ID'].isin(junction_ids) | 
                                            gdf['TO_INTERSECTION_ID'].isin(junction_ids)]
                self.junction_ids = filtered_centreline_gdf['FROM_INTERSECTION_ID'].unique().tolist() + filtered_centreline_gdf['TO_INTERSECTION_ID'].unique().tolist()
                centreline_gdf = filtered_centreline_gdf

            if centreline_gdf is not None:
                # Process the centreline data
                processed_gdf = self.process_gdf(centreline_gdf, active_types)

                processed_gdf.to_file(self.shapefile_path)
                self.logger.info(f"Processed centreline data and saved to {self.shapefile_path}")
                
                self.centreline_gdf = processed_gdf

        except Exception as e:
            self.logger.error(f"Error in setup processing: {e}")
            return None

    def process_gdf(self, gdf, active_types):
        """
        Process the centreline data.
        Returns:
            geopandas.GeoDataFrame: Processed centreline data.
        """
        self.logger.info("Processing centreline data.")

        # Filter the DataFrame to include only relevant feature codes
        mask = gdf['FEATURE_CODE'].isin(active_types.keys())
        processed_gdf = gdf.loc[mask].copy()

        # Set values using .loc to avoid SettingWithCopyWarning
        processed_gdf.loc[:, 'nolanes'] = processed_gdf['FEATURE_CODE'].map(lambda x: active_types[x]['numLanes'])
        processed_gdf.loc[:, 'speed'] = processed_gdf['FEATURE_CODE'].map(lambda x: active_types[x]['speed'])
        processed_gdf.loc[:, 'DIR_TRAVEL'] = processed_gdf.apply(
            lambda row: 'B' if row['ONEWAY_DIR_CODE'] == 0 else ('F' if row['ONEWAY_DIR_CODE'] == 1 else 'T'), axis=1)

        # Rename columns to match the expected format for netconvert
        rename_dict = {
            'CENTRELINE_ID': 'LINK_ID',
            'LINEAR_NAME_FULL_LEGAL': 'ST_NAME',
            'FROM_INTERSECTION_ID': 'REF_IN_ID',
            'TO_INTERSECTION_ID': 'NREF_IN_ID',
            'FEATURE_CODE': 'FUNC_CLASS',
        }
        processed_gdf.rename(columns=rename_dict, inplace=True)

        # Select only the required fields to ensure the DataFrame is correctly formatted for netconvert
        required_fields = ['LINK_ID', 'ST_NAME', 'REF_IN_ID', 'NREF_IN_ID', 'FUNC_CLASS', 'speed', 'nolanes', 'DIR_TRAVEL', 'geometry']
        
        required_gdf = processed_gdf.loc[:, required_fields]
        return required_gdf

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
