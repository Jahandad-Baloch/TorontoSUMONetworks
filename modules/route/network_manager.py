from scripts.data_integration.lane_closure import LaneClosure
from scripts.traffic_data_processing.network_parser import NetworkParser
from scripts.common.centreline_processor import CentrelineProcessor
from modules.core.app_context import AppContext
from modules.core.network_base import NetworkBase

""" 
Description: This module is responsible for managing the SUMO network data.
path: scripts/sumo_tools/network_manager.py
"""

class NetworkManager(NetworkBase):
    """Manages the SUMO network data operations.

    Args:
        app_context (AppContext): Central application context.
    """
    def __init__(self, app_context: AppContext) -> None:
        super().__init__(app_context)
        self.lane_closure = LaneClosure(app_context)
        self.network_parser = NetworkParser(app_context)
        self.centreline_processor = CentrelineProcessor(app_context)
        
    def get_lane_closure_data(self) -> object:
        """Retrieves lane closure data.

        Returns:
            pd.DataFrame: The lane closure data.
        """
        lane_closure_data = self.lane_closure.get_lane_closure_data()
        return lane_closure_data

    def get_edge_ids_affected_by_lane_closure(self, lane_closure_data: object) -> list:
        """Determines edge IDs affected by lane closures.

        Args:
            lane_closure_data (pd.DataFrame): Lane closure data.

        Returns:
            list: Edge IDs.
        """
        centreline_ids = lane_closure_data['CENTRELINE_ID'].unique().tolist()
        edge_ids = self.network_parser.get_edge_ids_from_centreline_ids(centreline_ids)
        return edge_ids

    def generate_lane_closure_data(self, lane_closure_data: object) -> object:
        """Generates lane closure data for affected edges.

        Args:
            lane_closure_data (pd.DataFrame): Lane closure data.

        Returns:
            pd.DataFrame: Modified lane closure data.
        """
        edge_ids = self.get_edge_ids_affected_by_lane_closure(lane_closure_data)
        lane_closure_data = self.lane_closure.generate_lane_closure_data(edge_ids, lane_closure_data)
        return lane_closure_data

    def save_lane_closure_data(self, lane_closure_data: object, output_file: str) -> None:
        """Saves lane closure data to a CSV file.

        Args:
            lane_closure_data (pd.DataFrame): Lane closure data.
            output_file (str): File path for output.
        """
        lane_closure_data.to_csv(output_file, index=False)
        self.logger.info(f"Lane closure data saved to: {output_file}")

    def apply_lane_closure_data(self, lane_closure_data: object) -> None:
        """Applies lane closure data to the network.

        Args:
            lane_closure_data (pd.DataFrame): Lane closure data.
        """
        self.lane_closure.apply_lane_closure_data(lane_closure_data)
        self.logger.info("Lane closure data applied to the network data.")