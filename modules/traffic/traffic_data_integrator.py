# modules/traffic/traffic_data_integrator.py
from typing import Dict, Any
import os
import pandas as pd

from modules.core.network_base import NetworkBase
from modules.network.network_parser import NetworkParser
from modules.traffic.traffic_data_processor import TrafficDataProcessor
from modules.traffic.xml_generator import XMLGenerator
from modules.traffic.weight_generator import WeightGenerator
from modules.common.utils import FileIO

class TrafficDataIntegrator(NetworkBase):
    """
    Integrates traffic data with the SUMO network and generates XML files for turning movements
    and edge weight files.

    Attributes:
        network_parser (:obj:`NetworkParser`): Parses the SUMO network file.
        traffic_processor (:obj:`TrafficDataProcessor`): Preprocesses the traffic volume data.
        xml_generator (:obj:`XMLGenerator`): Generates XML intervals and turning movements data.
        weight_generator (:obj:`WeightGenerator`): Creates edge weights XML files.
    """

    def __init__(self, app_context) -> None:
        """
        Initialize TrafficDataIntegrator using the provided application context.

        Args:
            app_context (:obj:`AppContext`): The central application context containing configuration and logger.
        """
        # Initialize parent using context configuration if needed
        super().__init__(app_context)
        self.app_context = app_context

        self.config = self.app_context.config
        self.logger = self.app_context.logger

        self.network_parser = NetworkParser(self.net_file, self.logger)
        self.traffic_processor = TrafficDataProcessor(
            self.traffic_volume_file,
            self.traffic_settings,
            self.logger
        )
        self.xml_generator = XMLGenerator(self.logger)
        self.weight_generator = WeightGenerator(self.logger)

    def execute(self) -> None:
        """
        Execute the traffic data integration process.
        
        This method:
          1. Loads the SUMO network.
          2. Preprocesses traffic data for each mode.
          3. Generates XML files for turning movements.
          4. Generates edge weight files.
        """
        # Parse the network file.
        self.network_parser.load_network()
        edge_data = self.network_parser.edges

        for mode in self.modes:
            self.files_by_mode[mode] = {
                'turning_movements': os.path.join(
                    self.processing_outputs, f'turning_movements_{mode}.xml'
                ),
                'edge_weights': os.path.join(
                    self.processing_outputs, f'edge_weights_{mode}'
                )
            }

            # Preprocess traffic data for the current mode.
            traffic_data: pd.DataFrame = self.traffic_processor.preprocess_traffic_data(mode)

            # Save processed traffic data to CSV for reference.
            FileIO.save_to_csv(
                traffic_data,
                os.path.join(self.processing_outputs, f'traffic_data_{mode}.csv'),
                self.logger
            )

            # Prepare junctions with correct edge-to-direction mappings.
            junctions_with_directions_df = self._prepare_junctions_with_directions()

            # Create time intervals for the traffic data.
            root, intervals = self.xml_generator.create_intervals(traffic_data)

            # Process traffic data to generate turning movements.
            self.xml_generator.process_traffic_data(
                traffic_data.groupby(['time_start', 'time_end']),
                junctions_with_directions_df,
                intervals,
                edge_data,
                mode
            )

            # Save the turning movements to an XML file.
            self.xml_generator.save_xml_file(root, self.files_by_mode[mode]['turning_movements'])

            # Generate edge weight files.
            os.makedirs(os.path.dirname(self.files_by_mode[mode]['edge_weights']), exist_ok=True)
            self.weight_generator.generate_weights_files(
                self.files_by_mode[mode]['turning_movements'],
                self.files_by_mode[mode]['edge_weights']
            )

            self.logger.info(f"Completed processing for mode: {mode}")

    def _prepare_junctions_with_directions(self) -> pd.DataFrame:
        """
        Prepare a DataFrame containing junction data with computed directional mappings.

        Returns:
            :obj:`pd.DataFrame`: DataFrame with junction IDs, coordinates, and computed directions.
        """
        junctions_df = pd.DataFrame.from_dict(self.network_parser.junctions, orient='index').reset_index()
        junctions_df.columns = ['junction_id', 'x', 'y', 'incLanes', 'edge_ids']
        junctions_df = junctions_df.astype({
            'junction_id': 'str',
            'x': 'float',
            'y': 'float',
            'incLanes': 'str',
            'edge_ids': 'str'
        })

        # Compute cardinal directions for each junction.
        junctions_df['directions'] = junctions_df['edge_ids'].apply(
            lambda ids: '|'.join([self._get_cardinal_direction(edge_id) for edge_id in ids.split('|')])
        )
        # Save the computed junctions data for debugging or reference.
        FileIO.save_to_csv(junctions_df, self.junction_directions_path, self.logger)
        return junctions_df

    def _get_cardinal_direction(self, edge_id: str) -> str:
        """
        Retrieve the cardinal direction for a given edge ID from the parsed network data.

        Args:
            edge_id (str): The edge identifier.

        Returns:
            str: The cardinal direction (e.g., 'nb', 'sb', 'eb', 'wb') or 'unknown'.
        """
        if edge_id in self.network_parser.edges:
            connections = self.network_parser.edges[edge_id].get('connections', [])
            if connections:
                return connections[0].get('cardinal_direction', 'unknown')
        return 'unknown'

