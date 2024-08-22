from scripts.traffic_data_processing.network_parser import NetworkParser
from scripts.traffic_data_processing.traffic_data_processor import TrafficDataProcessor
from scripts.traffic_data_processing.junction_matcher import JunctionMatcher, CoordinateTransformer
from scripts.traffic_data_processing.direction_calculator import DirectionCalculator
from scripts.traffic_data_processing.xml_generator import XMLGenerator
from scripts.traffic_data_processing.weight_generator import WeightGenerator
from scripts.common.utils import FileIO
from scripts.common.network_base import NetworkBase
import os

""" 
This script processes the traffic data and generates the SUMO network.
path: scripts/traffic_data_processing/main_processor.py
"""

class MainProcessor(NetworkBase):
    def __init__(self, config_file: str):
        super().__init__(config_file)
        self.prepare_directories()

        self.network_parser = NetworkParser(self.net_file, self.logger)
        self.network_parser.load_network()
        
        self.traffic_processor = TrafficDataProcessor(self.traffic_volume_file, self.traffic_settings, self.logger)
        self.coordinate_transformer = CoordinateTransformer(self.network_parser.proj_parameter, self.network_parser.net_offset_x, self.network_parser.net_offset_y)
        self.junction_matcher = JunctionMatcher(self.network_parser.junctions, self.coordinate_transformer, self.traffic_settings, self.logger)
        self.direction_calculator = DirectionCalculator(self.network_parser.edges, self.traffic_settings, self.logger)
        self.xml_generator = XMLGenerator(self.logger)
        self.weight_generator = WeightGenerator(self.logger)


    def process_network(self):
        directions_df = self.direction_calculator.calculate_directions()
        FileIO.save_to_csv(directions_df, self.processing_outputs + '/edge_directions.csv', self.logger)

        traffic_data = self.traffic_processor.preprocess_traffic_data()
        node_to_junction_id = self.junction_matcher.find_nearest_junction(traffic_data)
        FileIO.save_to_csv(node_to_junction_id, self.processing_outputs + '/node_junction_mapping.csv', self.logger)

        junctions_with_directions_df = self.junction_matcher.get_inc_edges(node_to_junction_id, self.direction_calculator.edge_directions)
        FileIO.save_to_csv(junctions_with_directions_df, self.processing_outputs + '/junction_directions.csv', self.logger)

        root, intervals = self.xml_generator.create_intervals(traffic_data)
        self.xml_generator.process_traffic_data(traffic_data.groupby(['time_start', 'time_end']), junctions_with_directions_df, intervals, self.network_parser.connections, self.traffic_settings['mode'])
        self.xml_generator.save_xml_file(root, self.processing_outputs + '/turning_movements.xml')

        # create weight prefix path
        weight_prefix = os.path.join(self.processing_outputs, 'edge_weights')
        os.makedirs(os.path.dirname(weight_prefix), exist_ok=True)

        self.weight_generator.generate_weights_files(self.processing_outputs + '/turning_movements.xml', weight_prefix)
        self.logger.info("Network processing completed")
        self.logger.info(f"\n.......................\n")

if __name__ == "__main__":
    processor = MainProcessor('configurations/main_config.yaml')
    processor.process_network()
