import xml.etree.ElementTree as ET
from collections import defaultdict

class WeightGenerator:
    def __init__(self, logger):
        self.logger = logger

    def generate_weights_files(self, turn_counts_file: str, output_path: dict):
        interval_counts = self.parse_turn_counts(turn_counts_file)

        begin = int(list(interval_counts.keys())[0].split('to')[0])
        end = int(list(interval_counts.keys())[-1].split('to')[1])

        all_edges = defaultdict(int)
        for interval_id, edge_counts in interval_counts.items():
            for edge, count in edge_counts.items():
                all_edges[edge] += count

        total_count = sum(all_edges.values())

        via_weights = {edge: count * 0.7 for edge, count in all_edges.items()}
        source_weights = {edge: count * 0.2 for edge, count in all_edges.items()}
        destination_weights = {edge: count * 0.1 for edge, count in all_edges.items()}

        self._write_weights_file(output_path + '.via.xml', via_weights, begin, end)
        self._write_weights_file(output_path + '.src.xml', source_weights, begin, end)
        self._write_weights_file(output_path + '.dst.xml', destination_weights, begin, end)

        self.logger.info(f"Weight files have been generated")
        self.logger.info(f"Via edges: {len(via_weights)}, Src edges: {len(source_weights)}, Dst edges: {len(destination_weights)}")

    def parse_turn_counts(self, turn_counts_file: str):
        tree = ET.parse(turn_counts_file)
        root = tree.getroot()
        
        interval_counts = {}
        for interval in root.findall('interval'):
            interval_id = interval.get('id')
            edge_counts = defaultdict(int)
            
            for edge_relation in interval.findall('edgeRelation'):
                from_edge = edge_relation.get('from')
                to_edge = edge_relation.get('to')
                count = int(edge_relation.get('count'))
                
                edge_counts[from_edge] += count
                edge_counts[to_edge] += count
            
            interval_counts[interval_id] = edge_counts
        
        return interval_counts

    def _write_weights_file(self, filename: str, weights: dict, begin: int, end: int):
        with open(filename, 'w') as file:
            file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            file.write('<edgedata>\n')
            file.write(f'  <interval begin="{begin}" end="{end}"/>\n')
            for edge, weight in weights.items():
                file.write(f'    <edge id="{edge}" value="{int(weight)}"/>\n')
            file.write('  </interval>\n')
            file.write('</edgedata>\n')
