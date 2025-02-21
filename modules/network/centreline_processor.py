# modules/network/centreline_processor.py
import os
import geopandas as gpd
from typing import Optional

class CentrelineProcessor:
    """
    Processes centreline geojson data for building the SUMO network.
    
    Attributes:
        geojson_file (str): Path to the geojson file.
        logger (logging.Logger): Logger for status messages.
        centreline_gdf (Optional[gpd.GeoDataFrame]): Processed GeoDataFrame after filtering.
        junction_ids (list): Junction IDs extracted during processing.
    """
    def __init__(self, geojson_file: str, logger) -> None:
        """
        Initializes the CentrelineProcessor.

        Args:
            geojson_file (str): Path to the centreline geojson file.
            logger (logging.Logger): Logger instance.
        """
        self.geojson_file = geojson_file
        self.logger = logger
        self.centreline_gdf = None
        self.junction_ids = []

    def filter_centreline_data(self, active_types: dict, network_area: str,
                               network_extent: str, paths: dict,
                               shapefile_path: Optional[str] = None,
                               junction_ids: Optional[list] = None) -> Optional[gpd.GeoDataFrame]:
        """
        Processes and filters the centreline data based on active types and network extent.

        Args:
            active_types (dict): Mapping of active feature codes and their attributes.
            network_area (str): The area name for filtering.
            network_extent (str): The extent (e.g., 'city_wide', 'by_ward_name', etc.).
            paths (dict): Dictionary of relevant paths.
            shapefile_path (Optional[str]): Destination path for saving the shapefile.
            junction_ids (Optional[list]): Junction IDs to filter by when extent is 'by_junctions'.

        Returns:
            Optional[gpd.GeoDataFrame]: Processed GeoDataFrame or None if an error occurs.
        """
        try:
            gdf = gpd.read_file(self.geojson_file)
            self.logger.info(f"Processing centreline data for: {network_area} ({network_extent}).")
            if network_extent == 'city_wide':
                centreline_gdf = gdf
            elif network_extent in ['by_ward_name', 'by_neighbourhood', 'by_neighborhood']:
                centreline_gdf = self.get_boundaries_gdf(paths, network_extent, network_area, gdf)

            elif network_extent == 'by_junctions':
                if not junction_ids:
                    self.logger.error("No junction IDs provided for 'by_junctions' network extent.")
                    return None
                centreline_gdf = gdf[gdf['FROM_INTERSECTION_ID'].isin(junction_ids) | 
                                     gdf['TO_INTERSECTION_ID'].isin(junction_ids)]

            else:
                self.logger.error("Unsupported network extent.")
                return None

            self.junction_ids = list(set(
                centreline_gdf['FROM_INTERSECTION_ID'].tolist() +
                centreline_gdf['TO_INTERSECTION_ID'].tolist()
            ))
            
            if centreline_gdf is not None:
                processed_gdf = self.process_gdf(centreline_gdf, active_types)
                if shapefile_path:
                    processed_gdf.to_file(shapefile_path)
                    self.logger.info(f"Processed centreline data saved to {shapefile_path}")
                self.centreline_gdf = processed_gdf
                return processed_gdf
        except Exception as e:
            self.logger.error(f"Error processing centreline data: {e}")
            return None

    def get_boundaries_gdf(self, paths: dict, network_extent: str,
                           network_area: str, gdf: gpd.GeoDataFrame) -> Optional[gpd.GeoDataFrame]:
        """
        Loads boundaries and filters the centreline data to the specified area.

        Args:
            paths (dict): Dictionary containing paths.
            network_extent (str): Extent type for boundaries.
            network_area (str): The area name.
            gdf (gpd.GeoDataFrame): Original centreline GeoDataFrame.

        Returns:
            Optional[gpd.GeoDataFrame]: Filtered GeoDataFrame or None.
        """
        boundaries_dir = os.path.join(paths['raw_data'], 'city-wards' if network_extent == 'by_ward_name'
                                       else 'neighbourhoods')
        try:
            for file in os.listdir(boundaries_dir):
                if file.endswith('4326.geojson'):
                    boundaries_file = os.path.join(boundaries_dir, file)
                    boundaries_gdf = gpd.read_file(boundaries_file)
                    # Debug: list available boundary names
                    # self.logger.info(f"Available area names in boundaries: {boundaries_gdf['AREA_NAME'].unique().tolist()}")
                    return self.get_centreline_for_area(network_area, boundaries_gdf, gdf)
        except Exception as e:
            self.logger.error(f"Error loading boundaries from {boundaries_dir}: {e}")
            return None

    def process_gdf(self, gdf: gpd.GeoDataFrame, active_types: dict) -> gpd.GeoDataFrame:
        """
        Processes the GeoDataFrame by filtering and mapping feature attributes.

        Args:
            gdf (gpd.GeoDataFrame): Original centreline GeoDataFrame.
            active_types (dict): Active feature types with lane and speed attributes.

        Returns:
            gpd.GeoDataFrame: Processed GeoDataFrame ready for netconvert.
        """
        self.logger.info("Filtering and processing centreline GeoDataFrame.")
        mask = gdf['FEATURE_CODE'].isin(active_types.keys())
        processed_gdf = gdf.loc[mask].copy()
        processed_gdf['nolanes'] = processed_gdf['FEATURE_CODE'].map(lambda x: active_types[x]['numLanes'])
        processed_gdf['speed'] = processed_gdf['FEATURE_CODE'].map(lambda x: active_types[x]['speed'])
        processed_gdf['DIR_TRAVEL'] = processed_gdf.apply(
            lambda row: 'B' if row['ONEWAY_DIR_CODE'] == 0 else ('F' if row['ONEWAY_DIR_CODE'] == 1 else 'T'),
            axis=1
        )
        rename_dict = {
            'CENTRELINE_ID': 'LINK_ID',
            'LINEAR_NAME_FULL_LEGAL': 'ST_NAME',
            'FROM_INTERSECTION_ID': 'REF_IN_ID',
            'TO_INTERSECTION_ID': 'NREF_IN_ID',
            'FEATURE_CODE': 'FUNC_CLASS',
        }
        processed_gdf.rename(columns=rename_dict, inplace=True)
        required_fields = ['LINK_ID', 'ST_NAME', 'REF_IN_ID', 'NREF_IN_ID',
                           'FUNC_CLASS', 'speed', 'nolanes', 'DIR_TRAVEL', 'geometry']
        return processed_gdf.loc[:, required_fields]

    def get_centreline_for_area(self, area_name: str,
                                boundaries_gdf: gpd.GeoDataFrame,
                                centreline_gdf: gpd.GeoDataFrame) -> Optional[gpd.GeoDataFrame]:
        """
        Filters the centreline data to the specified area using boundaries.

        Args:
            area_name (str): Name of the area.
            boundaries_gdf (gpd.GeoDataFrame): GeoDataFrame containing boundary polygons.
            centreline_gdf (gpd.GeoDataFrame): Original centreline data.

        Returns:
            Optional[gpd.GeoDataFrame]: Filtered GeoDataFrame or None if an error occurs.
        """
        
        try:
            # Perform a case-insensitive matching of area names
            matched_boundaries = boundaries_gdf[boundaries_gdf['AREA_NAME'].str.lower() == area_name.lower().replace('_', ' ')]
            self.logger.info(f"Matched boundaries for area '{area_name}': {len(matched_boundaries)} found.")
            if matched_boundaries.empty:
                self.logger.error(f"No boundaries found matching area name: {area_name}")
                return None
            area_polygon = matched_boundaries.iloc[0]['geometry']
            intersecting_gdf = centreline_gdf[centreline_gdf.intersects(area_polygon)]
            return intersecting_gdf
        except Exception as e:
            self.logger.error(f"Error filtering centreline for area {area_name}: {e}")
            return None
