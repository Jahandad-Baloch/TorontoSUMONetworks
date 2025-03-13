# modules/traffic/traffic_data_integrator.py
from typing import Any
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
    Integrates traffic data with the SUMO network and generates XML files 
    for turning movements (TMC) and midblock flows (SVC), then edge weight files.
    """

    def __init__(self, app_context) -> None:
        super().__init__(app_context)
        self.app_context = app_context

        self.config = self.app_context.config
        self.logger = self.app_context.logger
        
        # Parse the SUMO network
        self.network_parser = NetworkParser(self.net_file, self.logger)

        # Process TMC & SVC data
        self.traffic_processor = TrafficDataProcessor(
            self.tmc_data_file,
            self.svc_data_file,
            self.traffic_settings,
            self.logger
        )

        # Generators
        self.xml_generator = XMLGenerator(self.logger)
        self.weight_generator = WeightGenerator(self.logger)

    def execute(self) -> None:
        """
        Main entry: 
          1) Load SUMO network.
          2) For each mode, preprocess intersection (TMC) and midblock (SVC) data.
          3) Generate XML files for intersection turning movements, plus optional midblock flows.
          4) Generate edge weight files from intersection + midblock data if needed.
        """
        self.logger.info("Loading network...")
        self.network_parser.load_network()
        edge_data = self.network_parser.edges

        # 1) Prepare network-based directions
        junctions_with_directions_df = self._prepare_junctions_with_directions()

        for mode in self.modes:
            # Filenames to store the resulting XMLs
            self.files_by_mode[mode] = {
                'tmc_xml': os.path.join(self.processing_outputs, f'turning_movements_{mode}.xml'),
                'edge_weights': os.path.join(self.processing_outputs, f'edge_weights_{mode}')
            }

            # 2) Preprocess TMC data (intersection)
            intersection_data = self.traffic_processor.preprocess_tmc_data(mode)
            # Save for reference
            FileIO.save_to_csv(intersection_data,
                               os.path.join(self.processing_outputs, f'intersection_data_{mode}.csv'),
                               self.logger)



            # --- Intersection TMC XML Generation ---
            if not intersection_data.empty:
                tmc_root, tmc_intervals = self.xml_generator.create_intervals(intersection_data)
                self.xml_generator.process_tmc_traffic(
                    intersection_data.groupby(['time_start', 'time_end']),
                    junctions_with_directions_df,
                    tmc_intervals,
                    edge_data,
                    mode
                )
                self.xml_generator.save_xml_file(tmc_root, self.files_by_mode[mode]['tmc_xml'])
            else:
                self.logger.warning(f"No intersection data found for mode {mode}.")


            # 4) Edge Weight Generation
            # The weight generator can parse both TMC and SVC XMLs to compute final weights
            os.makedirs(os.path.dirname(self.files_by_mode[mode]['edge_weights']), exist_ok=True)
            self.weight_generator.generate_weights_files(
                self.files_by_mode[mode]['tmc_xml'], 
                self.files_by_mode[mode]['edge_weights']
            )

            self.logger.info(f"Completed processing for mode: {mode}")

        # # Preprocess SVC data (midblock)
        # midblock_data = self.traffic_processor.preprocess_svc_data()
        # svc_xml = os.path.join(self.processing_outputs, 'midblock_volumes.xml')

        # FileIO.save_to_csv(midblock_data,
        #                     os.path.join(self.processing_outputs, f'midblock_data.csv'),
        #                     self.logger)

        # # --- Midblock SVC XML Generation ---
        # if not midblock_data.empty:
        #     svc_root, svc_intervals = self.xml_generator.create_intervals(midblock_data)
        #     self.xml_generator.process_svc_traffic(
        #         midblock_data.groupby(['time_start', 'time_end']),
        #         svc_intervals,
        #         edge_data
        #     )
        #     self.xml_generator.save_xml_file(svc_root, svc_xml)
        # else:
        #     self.logger.warning(f"No midblock data found.")

    def _prepare_junctions_with_directions(self) -> pd.DataFrame:
        """
        Return a DataFrame with each junction ID, x, y, incLanes, edge_ids,
        and 'directions' assigned from the parsed network.
        """
        junctions_df = pd.DataFrame.from_dict(self.network_parser.junctions, orient='index').reset_index()
        junctions_df.columns = ['junction_id', 'x', 'y', 'incLanes', 'edge_ids', 'directions']
        junctions_df = junctions_df.astype({
            'junction_id': 'str',
            'x': 'float',
            'y': 'float',
            'incLanes': 'str',
            'edge_ids': 'str'
        })
        # Save for debugging
        # FileIO.save_to_csv(junctions_df, self.junction_directions_path, self.logger)
        return junctions_df
