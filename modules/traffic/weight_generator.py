import xml.etree.ElementTree as ET
from collections import defaultdict

class WeightGenerator:
    """Generates XML files containing edge weights for intersections and midblocks.

    Args:
        logger: Logger instance.
    """
    def __init__(self, logger) -> None:
        self.logger = logger

    def generate_weights_files(self, turn_counts_file: str, output_path: str, midblock_counts_file: str = None) -> None:
        """Generate weight files based on turning movement data (TMC) and optional midblock traffic data (SVC).

        Args:
            turn_counts_file (str): XML file with intersection turning movement data.
            output_path (str): Base path for output weight files.
            midblock_counts_file (str, optional): XML file with midblock volume data.
                                                 Defaults to None if not available.
        """
        # Parse the turning movements file to extract interval info and edge counts
        intervals_data = self.parse_counts(turn_counts_file)
        
        midblock_counts_file = None
        # If midblock data is provided, parse and combine with intersection data
        if midblock_counts_file:
            midblock_data = self.parse_counts(midblock_counts_file)
            # Combine interval counts from both sources
            for interval_id, interval_info in midblock_data.items():
                if interval_id in intervals_data:
                    # Add midblock counts to existing intervals
                    for edge, count in interval_info['edge_counts'].items():
                        intervals_data[interval_id]['edge_counts'][edge] = intervals_data[interval_id]['edge_counts'].get(edge, 0) + count
                else:
                    # Add new intervals from midblock data
                    intervals_data[interval_id] = interval_info

        if not intervals_data:
            self.logger.error("No intervals found in the provided data files.")
            return

        # Get all interval IDs sorted chronologically
        interval_ids = sorted(intervals_data.keys())
        
        # Calculate each edge's total weight across all intervals
        all_edges = defaultdict(int)
        for interval_id in interval_ids:
            for edge, count in intervals_data[interval_id]['edge_counts'].items():
                all_edges[edge] += count

        # Generate different weight types (via, source, destination)
        via_weights = {edge: count * 0.7 for edge, count in all_edges.items()}
        source_weights = {edge: count * 0.2 for edge, count in all_edges.items()}
        destination_weights = {edge: count * 0.1 for edge, count in all_edges.items()}

        # Generate the weight files with proper intervals
        self._write_weights_file(output_path + '.via.xml', via_weights, intervals_data)
        self._write_weights_file(output_path + '.src.xml', source_weights, intervals_data)
        self._write_weights_file(output_path + '.dst.xml', destination_weights, intervals_data)

        self.logger.info(f"Weight files have been generated for {len(interval_ids)} intervals")
        self.logger.info(f"Via edges: {len(via_weights)}, Src edges: {len(source_weights)}, Dst edges: {len(destination_weights)}")

    def parse_counts(self, counts_file: str) -> dict:
        """Parse the traffic movement XML to extract edge counts from intersections and midblocks.

        Args:
            counts_file (str): Path to traffic movement XML.
        
        Returns:
            dict: Mapping of intervals to edge counts and time info.
        """
        tree = ET.parse(counts_file)
        root = tree.getroot()
        
        intervals_data = {}
        for interval in root.findall('interval'):
            interval_id = interval.get('id')
            begin_time = interval.get('begin')
            end_time = interval.get('end')
            
            # Skip intervals with invalid time values
            try:
                begin_value = int(begin_time)
                end_value = int(end_time)
                if begin_value >= end_value:
                    self.logger.warning(f"Skipping invalid interval {interval_id}: begin={begin_time}, end={end_time}")
                    continue
            except (ValueError, TypeError):
                self.logger.warning(f"Skipping interval {interval_id} with non-numeric time values: begin={begin_time}, end={end_time}")
                continue
            
            edge_counts = defaultdict(int)
            for edge_relation in interval.findall('edgeRelation'):
                from_edge = edge_relation.get('from')
                to_edge = edge_relation.get('to')
                count = int(edge_relation.get('count'))
                
                edge_counts[from_edge] += count
                edge_counts[to_edge] += count
            
            intervals_data[interval_id] = {
                'begin': begin_time,
                'end': end_time,
                'edge_counts': edge_counts
            }
        
        # Log the number of valid intervals found
        self.logger.info(f"Found {len(intervals_data)} valid intervals in {counts_file}")
        
        return intervals_data

    def _write_weights_file(self, filename: str, weights: dict, intervals_data: dict) -> None:
        """Write the weights to an XML file with proper intervals.

        Args:
            filename (str): Output file name.
            weights (dict): Dictionary of edge weights.
            intervals_data (dict): Information about time intervals.
        """
        # Create the root element
        root = ET.Element('edgedata')
        
        # Sort intervals chronologically by their ID
        interval_ids = sorted(intervals_data.keys())
        
        # Add an interval element for each interval in the source data
        for interval_id in interval_ids:
            interval_info = intervals_data[interval_id]
            begin_time = interval_info['begin']
            end_time = interval_info['end']
            
            # Create interval element with proper attributes
            interval_elem = ET.SubElement(root, 'interval', {
                'id': interval_id,
                'begin': begin_time,
                'end': end_time
            })
            
            # Add edge elements for this interval
            for edge_id, weight in weights.items():
                # Check if this edge had any activity in this specific interval
                if edge_id in interval_info['edge_counts']:
                    edge_elem = ET.SubElement(interval_elem, 'edge')
                    edge_elem.set('id', edge_id)
                    edge_elem.set('value', str(int(weight)))
                    
        # Write the XML to file with pretty printing
        self._write_xml_file(filename, root)
    
    def _write_xml_file(self, filename: str, root: ET.Element) -> None:
        """Write the XML element to a file with pretty printing.

        Args:
            filename (str): Output file name.
            root (ET.Element): Root XML element to write.
        """
        # Convert to string with pretty printing
        rough_string = ET.tostring(root, 'utf-8')
        reparsed = ET.fromstring(rough_string)  # Reparse to add indentation
        
        # Manual pretty printing (since minidom can be inconsistent)
        xml_text = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml_text.append('<edgedata>')
        
        # Process each interval
        for interval in reparsed.findall('interval'):
            interval_str = f'  <interval id="{interval.get("id")}" begin="{interval.get("begin")}" end="{interval.get("end")}">'
            xml_text.append(interval_str)
            
            # Add edge elements
            for edge in interval.findall('edge'):
                edge_str = f'    <edge id="{edge.get("id")}" value="{edge.get("value")}"/>'
                xml_text.append(edge_str)
                
            xml_text.append('  </interval>')
            
        xml_text.append('</edgedata>')
        
        # Write to file
        with open(filename, 'w', encoding='utf-8') as file:
            file.write('\n'.join(xml_text))
            
        self.logger.info(f"Weight file saved to {filename}")
