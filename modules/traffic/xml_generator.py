# modules/traffic/xml_generator.py
import xml.etree.ElementTree as ET
from xml.dom import minidom
import pandas as pd
from typing import Dict, Tuple, Any
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

    def create_intervals(self, traffic_data: pd.DataFrame) -> Tuple[ET.Element, Any]:
        """
        Create XML intervals based on unique time periods in the traffic data.

        Args:
            traffic_data (pd.DataFrame): Processed traffic data containing 'time_start' and 'time_end' columns.

        Returns:
            Tuple[ET.Element, Any]:
                - The root XML element.
                - A list of interval elements.
        """
        root = ET.Element("intervals")
        intervals = []  # placeholder for interval elements
        time_intervals = traffic_data[['time_start', 'time_end']].drop_duplicates().sort_values(by='time_start')
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
        self.logger.info("Created intervals for XML generation")
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

        Args:
            grouped_traffic_data: Grouped traffic data (by time intervals).
            junctions_df (pd.DataFrame): DataFrame with junction and direction mappings.
            intervals (Any): List of interval elements.
            edge_data (dict): Parsed network edge data.
            mode (str): Traffic mode (e.g., 'cars', 'truck', etc.).
        """
        self.logger.info(f"Starting processing for {mode} mode.")
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
                directions = junc_row['directions'].iloc[0].split('|')

                for edge_id, direction in zip(edges, directions):
                    if edge_id not in edge_data or 'connections' not in edge_data[edge_id]:
                        continue
                    for conn in edge_data[edge_id]['connections']:
                        to_edge = conn['to_lane'].split('_')[0]
                        feature_name = f"{direction}_{mode}_{conn.get('dir', 'X')}"
                        if feature_name not in row:
                            continue
                        count = row[feature_name]
                        relation_key = (edge_id, to_edge, count)
                        if relation_key in processed_relations:
                            self.logger.debug(f"Duplicate relation skipped: {relation_key}")
                            continue
                        edge_relation = ET.SubElement(current_interval, "edgeRelation")
                        edge_relation.set("from", edge_id)
                        edge_relation.set("to", to_edge)
                        edge_relation.set("count", str(count))
                        processed_relations.add(relation_key)

            # self.logger.info(f"Processed interval {interval_id} with {len(processed_relations)} relations.")
        self.logger.info(f"Completed processing for mode {mode} with {len(intervals)} intervals.")

    def save_xml_file(self, root: ET.Element, file_path: str) -> None:
        """
        Save the generated XML structure to a file.

        Args:
            root (ET.Element): Root XML element.
            file_path (str): Destination file path.
        """
        with open(file_path, "w") as f:
            f.write(self.prettify(root))
        self.logger.info(f"XML file saved to {file_path}")

    @staticmethod
    def prettify(elem: ET.Element) -> str:
        """
        Return a pretty-printed XML string for the Element.

        Args:
            elem (ET.Element): XML element to prettify.

        Returns:
            str: Pretty-printed XML string.
        """
        rough_string = ET.tostring(elem, "utf-8")
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

