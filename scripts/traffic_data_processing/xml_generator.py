import xml.etree.ElementTree as ET
from xml.dom import minidom
import pandas as pd
from typing import Dict, Tuple

""" 
Description: This script is used to generate XML files for traffic movements data.
path: scripts/traffic_data_processing/xml_generator.py
"""

class XMLGenerator:
    def __init__(self, logger):
        self.logger = logger

    def create_intervals(self, traffic_data: pd.DataFrame) -> Tuple[ET.Element, Dict[str, ET.Element]]:
        intervals = {}
        time_intervals = traffic_data[['time_start', 'time_end']].drop_duplicates().sort_values(by='time_start')
        
        root = ET.Element("data")
        for _, interval in time_intervals.iterrows():
            interval_id = f"{int(interval['time_start'])}to{int(interval['time_end'])}"
            intervals[interval_id] = ET.SubElement(root, "interval", id=interval_id, begin=str(interval['time_start']), end=str(interval['time_end']))
        
        return root, intervals

    def process_traffic_data(self, grouped_traffic_data: pd.DataFrame, 
                            junctions_with_directions_df: pd.DataFrame, 
                            intervals: Dict[str, ET.Element], 
                            edge_data: dict, mode: str):
        
        self.logger.info(f"Starting traffic data processing with {len(grouped_traffic_data)} groups")

        # Process the traffic data for each time interval
        for (time_start, time_end), group in grouped_traffic_data:

            interval_id = f"{int(time_start)}to{int(time_end)}"
            if interval_id in intervals:
                current_interval = intervals[interval_id]
                processed_edge_relations = set()

                # Process the traffic data for each junction
                for _, traffic_data in group.iterrows():
                    junction_row = junctions_with_directions_df[junctions_with_directions_df['junction_id'] == str(traffic_data['centreline_id'])]

                    if junction_row.empty:
                        continue

                    edges = str(junction_row['edge_ids'].iloc[0]).split('|')
                    directions = str(junction_row['directions'].iloc[0]).split('|')

                    # Process the traffic data for each edge
                    for edge_id, direction in zip(edges, directions):
                        if edge_id in edge_data and 'connections' in edge_data[edge_id]:  # Ensure connections are present
                            for connection in edge_data[edge_id]['connections']:
                                to_edge = connection['to_lane'].split('_')[0]  # Extract edge ID from to_lane
                                feature_name = f"{direction}_{mode}_{connection['dir']}"

                                if feature_name in traffic_data:  # Check if the feature exists in the traffic data
                                    
                                    count = traffic_data[feature_name]
                                    edge_relation_id = (edge_id, to_edge, count)

                                    if edge_relation_id not in processed_edge_relations:  # Check if the relation has been processed
                                        edge_relation = ET.SubElement(current_interval, "edgeRelation")
                                        edge_relation.set("from", edge_id)
                                        edge_relation.set("to", to_edge)
                                        edge_relation.set("count", str(count))
                                        processed_edge_relations.add(edge_relation_id)
                                    else:
                                        self.logger.debug(f"Duplicate relation skipped: {edge_relation_id}")

                self.logger.info(f"Processed traffic data for interval {interval_id} with {len(processed_edge_relations)} edge relations")
            else:
                self.logger.warning(f"Interval ID {interval_id} not found in intervals dictionary.")

        self.logger.info("Completed processing of traffic data.")

    def save_xml_file(self, root: ET.Element, file_path: str):
        with open(file_path, "w") as f:
            f.write(self.prettify(root))
        self.logger.info(f"XML traffic movements data has been saved to {file_path}")

    @staticmethod
    def prettify(elem: ET.Element) -> str:
        rough_string = ET.tostring(elem, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

