import xml.etree.ElementTree as ET
from xml.dom import minidom
import pandas as pd
from typing import Tuple, Any
import logging

class XMLGenerator:
    """
    Generates XML files for traffic movements based on processed traffic data.
    """
    def __init__(self, logger: logging.Logger) -> None:
        """
        Initialize the XMLGenerator.

        Args:
            logger (logging.Logger): Logger for status and error messages.
        """
        self.logger = logger
        
        # Direction mapping from TMC format (n_appr) to SUMO format (nb)
        self.direction_mapping = {
            'n_appr': 'nb',
            's_appr': 'sb',
            'e_appr': 'eb',
            'w_appr': 'wb'
        }

    def create_intervals(self, traffic_data: pd.DataFrame) -> Tuple[ET.Element, Any]:
        """
        Create XML intervals based on unique time periods in the traffic data.
        """
        root = ET.Element("intervals")
        intervals = []
        
        # Filter out invalid time intervals where end time is less than or equal to start time
        valid_times = traffic_data[
            traffic_data['time_end'] > traffic_data['time_start']
        ][['time_start', 'time_end']]
        
        # Sort by start time and drop duplicates
        time_intervals = valid_times.drop_duplicates().sort_values(by='time_start')
        
        # Log the number of time intervals to be created
        self.logger.info(f"Creating {len(time_intervals)} valid time intervals for XML generation")
        
        for _, interval in time_intervals.iterrows():
            interval_id = f"{int(interval['time_start'])}to{int(interval['time_end'])}"
            interval_elem = ET.SubElement(
                root,
                "interval",
                id=interval_id,
                begin=str(interval['time_start']),
                end=str(interval['time_end'])
            )
            intervals.append(interval_elem)
        
        # Log warning if any invalid intervals were filtered out
        invalid_count = len(traffic_data) - len(valid_times)
        if invalid_count > 0:
            self.logger.warning(f"Filtered out {invalid_count} invalid time intervals where end time <= start time")
        
        return root, intervals

    def process_traffic_data(
        self,
        grouped_traffic_data: pd.core.groupby.generic.DataFrameGroupBy,
        junctions_df: pd.DataFrame,
        intervals: Any,
        edge_data: dict,
        mode: str
    ) -> None:
        """
        Process grouped traffic data to generate XML turning movement elements.
        
        This method is kept for backward compatibility but delegates to the
        appropriate specialized method based on source type.
        """
        self.logger.info(f"Processing traffic data for mode: {mode}")
        self.process_tmc_traffic(grouped_traffic_data, junctions_df, intervals, edge_data, mode)

    def process_tmc_traffic(
        self,
        grouped_traffic_data: pd.core.groupby.generic.DataFrameGroupBy,
        junctions_df: pd.DataFrame,
        intervals: Any,
        edge_data: dict,
        mode: str
    ) -> None:
        """
        Process TMC (intersection) traffic data to generate XML turning movement elements.
        
        Args:
            grouped_traffic_data: Grouped TMC traffic data (by time intervals).
            junctions_df: DataFrame with junction and direction mappings.
            intervals: List of interval elements.
            edge_data: Parsed network edge data.
            mode: Traffic mode (e.g., 'cars', 'truck', etc.).
        """
        self.logger.info(f"Starting processing for {mode} mode (TMC data).")
        processed_count = 0
        
        for (time_start, time_end), group in grouped_traffic_data:
            interval_id = f"{int(time_start)}to{int(time_end)}"
            current_interval = next((interval for interval in intervals if interval.get('id') == interval_id), None)
            if current_interval is None:
                self.logger.warning(f"Interval {interval_id} missing; skipping group.")
                continue

            processed_relations = set()

            for _, row in group.iterrows():
                junc_row = junctions_df[junctions_df['junction_id'] == str(row['centreline_id'])]
                if junc_row.empty:
                    continue

                edges = junc_row['edge_ids'].iloc[0].split('|')
                
                # Handle 'directions' based on its type
                if isinstance(junc_row['directions'].iloc[0], list):
                    # If it's already a list, use it directly
                    directions = junc_row['directions'].iloc[0]
                else:
                    # If it's a string (from older versions or other sources), split it
                    try:
                        directions = junc_row['directions'].iloc[0].split('|')
                    except AttributeError:
                        self.logger.error(f"Cannot process directions for junction {row['centreline_id']}. Expected string or list, got: {type(junc_row['directions'].iloc[0])}")
                        continue

                # Ensure we have matching lengths for edges and directions
                if len(edges) != len(directions):
                    self.logger.warning(f"Mismatch in edges and directions count for junction {row['centreline_id']}: {len(edges)} edges vs {len(directions)} directions")
                    # Use shorter length to avoid index errors
                    min_length = min(len(edges), len(directions))
                    edges = edges[:min_length]
                    directions = directions[:min_length]

                for edge_id, direction in zip(edges, directions):
                    if edge_id not in edge_data or 'connections' not in edge_data[edge_id]:
                        continue
                        
                    for conn in edge_data[edge_id]['connections']:
                        to_edge = conn['to_lane'].split('_')[0]
                        
                        # Map TMC direction format to SUMO format if needed
                        tmc_direction = direction
                        if direction in self.direction_mapping.values():
                            # If direction is already in SUMO format (nb, sb, etc.), find corresponding TMC format
                            for tmc_dir, sumo_dir in self.direction_mapping.items():
                                if sumo_dir == direction:
                                    tmc_direction = tmc_dir
                                    break
                        
                        # Construct feature name using TMC format (e.g., n_appr_cars_r)
                        feature_name = f"{tmc_direction}_{mode}_{conn.get('dir', 'X')}"
                        
                        # For backward compatibility, also try SUMO format (e.g., nb_cars_r)
                        alt_feature_name = f"{direction}_{mode}_{conn.get('dir', 'X')}"
                        
                        if feature_name in row:
                            count = row[feature_name]
                        elif alt_feature_name in row:
                            count = row[alt_feature_name]
                        else:
                            continue
                            
                        relation_key = (edge_id, to_edge, count)
                        if relation_key in processed_relations:
                            continue
                            
                        edge_relation = ET.SubElement(current_interval, "edgeRelation")
                        edge_relation.set("from", edge_id)
                        edge_relation.set("to", to_edge)
                        edge_relation.set("count", str(count))
                        processed_relations.add(relation_key)
                        processed_count += 1

        self.logger.info(f"Completed processing for mode {mode} with {len(intervals)} intervals and {processed_count} relations.")

    def process_svc_traffic(
        self,
        grouped_traffic_data: pd.core.groupby.generic.DataFrameGroupBy,
        intervals: Any,
        edge_data: dict
    ) -> None:
        """
        Process SVC (midblock) traffic data to generate XML movement elements.
        
        Args:
            grouped_traffic_data: Grouped SVC traffic data (by time intervals).
            intervals: List of interval elements.
            edge_data: Parsed network edge data.
        """
        self.logger.info("Starting processing for SVC midblock data.")
        processed_count = 0
        
        for (time_start, time_end), group in grouped_traffic_data:
            interval_id = f"{int(time_start)}to{int(time_end)}"
            current_interval = next((interval for interval in intervals if interval.get('id') == interval_id), None)
            if current_interval is None:
                self.logger.warning(f"Interval {interval_id} missing; skipping group.")
                continue
                
            for _, row in group.iterrows():
                edge_id = str(row['centreline_id'])
                
                # Skip if this edge isn't in our network
                if edge_id not in edge_data:
                    continue
                    
                # For midblock data, the edge is both source and destination
                volume = row['volume_15min']
                if not pd.isna(volume):
                    edge_relation = ET.SubElement(current_interval, "edgeRelation")
                    edge_relation.set("from", edge_id)
                    edge_relation.set("to", edge_id)
                    edge_relation.set("count", str(int(volume)))
                    processed_count += 1
                    
        self.logger.info(f"Completed processing SVC data with {len(intervals)} intervals and {processed_count} relations.")

    def save_xml_file(self, root: ET.Element, file_path: str) -> None:
        """
        Save the generated XML structure to a file.
        """
        with open(file_path, "w") as f:
            f.write(self.prettify(root))
        self.logger.info(f"XML file saved to {file_path}")

    @staticmethod
    def prettify(elem: ET.Element) -> str:
        """
        Return a pretty-printed XML string for the Element.
        """
        rough_string = ET.tostring(elem, "utf-8")
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

