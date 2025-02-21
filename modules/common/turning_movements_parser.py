# scripts/simulation/turn_counts_parser.py
# Description: This script parses the turn counts from the SUMO output file.

import xml.etree.ElementTree as ET

class TurningMovementsParser:
    @staticmethod
    def parse_turn_counts(turn_counts_file):
        tree = ET.parse(turn_counts_file)
        root = tree.getroot()
        intervals = root.findall('interval')
        interval_counts = {}
        total_count = 0
        for interval in intervals:
            interval_id = interval.get('id')
            count = 0
            for edge_relation in interval:
                count += int(edge_relation.get('count'))
            interval_counts[interval_id] = count
            total_count += count
        return interval_counts, total_count