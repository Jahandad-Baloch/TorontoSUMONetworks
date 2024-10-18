from scripts.traffic_data_processing.network_parser import NetworkParser
from scripts.traffic_data_processing.traffic_data_processor import TrafficDataProcessor
from scripts.traffic_data_processing.xml_generator import XMLGenerator
from scripts.traffic_data_processing.weight_generator import WeightGenerator
from scripts.common.utils import FileIO
from scripts.common.network_base import NetworkBase
import os
import pandas as pd

""" 
Description: This script is used to integrate traffic data with the SUMO network.
path: scripts/traffic_data_processing/traffic_data_integrator.py
"""

class TrafficDataIntegrator(NetworkBase):
    def __init__(self, config_file: str):
        super().__init__(config_file)

        self.network_parser = NetworkParser(self.net_file, self.logger)
        self.traffic_processor = TrafficDataProcessor(self.traffic_volume_file, self.traffic_settings, self.logger)
        self.xml_generator = XMLGenerator(self.logger)
        self.weight_generator = WeightGenerator(self.logger)

    def integrate_data(self):
        # Load the network using NetworkParser
        self.network_parser.load_network()
        self.edge_data = self.network_parser.edges

        self.files_by_mode = {}
        traffic_data = {}
        for mode in self.modes:
            # Create file paths for turning movements and edge weights
            self.files_by_mode[mode] = {
                'turning_movements': os.path.join(self.processing_outputs, f'turning_movements_{mode}.xml'),
                'edge_weights': os.path.join(self.processing_outputs, f'edge_weights_{mode}')
            }

            # Preprocess traffic data for the current mode (cars, trucks, etc.)
            traffic_data = self.traffic_processor.preprocess_traffic_data(mode)

            # Save traffic data to CSV for reference
            FileIO.save_to_csv(traffic_data, os.path.join(self.processing_outputs, f'traffic_data_{mode}.csv'), self.logger)

            # Prepare the junctions with correct edge-to-direction mappings
            junctions_with_directions_df = self._prepare_junctions_with_directions()

            # Create time intervals for the traffic data
            root, intervals = self.xml_generator.create_intervals(traffic_data)

            # Process the traffic data to generate turning movements for each interval
            self.xml_generator.process_traffic_data(
                traffic_data.groupby(['time_start', 'time_end']), 
                junctions_with_directions_df, 
                intervals, 
                self.edge_data, 
                mode
            )

            # Save the turning movements to an XML file
            self.xml_generator.save_xml_file(root, self.files_by_mode[mode]['turning_movements'])

            # Generate edge weights files
            weight_prefix = os.path.join(self.processing_outputs, f'edge_weights_{mode}')
            os.makedirs(os.path.dirname(weight_prefix), exist_ok=True)
            self.weight_generator.generate_weights_files(self.files_by_mode[mode]['turning_movements'], weight_prefix)

            self.logger.info(f"Completed processing for mode: {mode}")

    
    def _prepare_junctions_with_directions(self):
        """Prepare the junctions with directions DataFrame by analyzing incoming edges and their connections."""
        junctions_with_directions_df = pd.DataFrame.from_dict(self.network_parser.junctions, orient='index').reset_index()
        junctions_with_directions_df.columns = ['junction_id', 'x', 'y', 'incLanes', 'edge_ids']

        junctions_with_directions_df = junctions_with_directions_df.astype({
            'junction_id': 'str',
            'x': 'float',
            'y': 'float',
            'incLanes': 'str',
            'edge_ids': 'str'
        })

        # Add directions by analyzing the edges and connections in the network
        # Apply it over the edge IDs instead of the incLanes
        junctions_with_directions_df['directions'] = junctions_with_directions_df['edge_ids'].apply(
            lambda edge_ids: '|'.join([self._get_cardinal_direction(edge_id) for edge_id in edge_ids.split('|')])
        )
        
        FileIO.save_to_csv(junctions_with_directions_df, self.junction_directions_path, self.logger)
        return junctions_with_directions_df
    
    def _get_cardinal_direction(self, edge_id):
        """Get the cardinal direction (sb, nb, eb, wb) for an edge based on edge connections."""
        if edge_id in self.edge_data and self.edge_data[edge_id]['connections']:
            return self.edge_data[edge_id]['connections'][0]['cardinal_direction']
        return 'unknown'

