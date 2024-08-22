# scripts/traffic_data_processing/network_parser.py
# Description: This script is used to parse the SUMO network file and extract the network elements such as edges, junctions, connections, and traffic light logic.

import xml.etree.ElementTree as ET
from collections import defaultdict

class NetworkParser:
    def __init__(self, network_file: str, logger):
        self.network_file = network_file
        self.logger = logger
        self.edges = {}
        self.junctions = {}
        self.connections = {}
        self.tl_logic = defaultdict(list)
        self.net_offset_x = 0.0
        self.net_offset_y = 0.0
        self.proj_parameter = ""
        self.epsg_code = ""

    def load_network(self):
        try:
            tree = ET.parse(self.network_file)
            root = tree.getroot()
            location = root.find('location')
            self.net_offset_x, self.net_offset_y = map(float, location.get('netOffset').split(','))
            self.proj_parameter = location.get('projParameter')
            self.epsg_code = self.proj_parameter.split('zone=')[1].split(' ')[0]

            for elem in root:
                if elem.tag == 'edge':
                    self._parse_edge(elem)
                elif elem.tag == 'junction' and elem.attrib.get('type') != 'internal':
                    self._parse_junction(elem)
                elif elem.tag == 'connection':
                    self._parse_connection(elem)
                elif elem.tag == 'tlLogic':
                    self._parse_tllogic(elem)
            self.logger.info(f"Loaded SUMO network elements from: {self.network_file}")
        except ET.ParseError as e:
            self.logger.error(f"Error parsing XML: {e}")

    def _parse_edge(self, elem: ET.Element):
        edge_id = elem.attrib['id']
        if 'function' not in elem.attrib and not edge_id.startswith('-'):
            from_node = elem.attrib.get('from')
            to_node = elem.attrib.get('to')
            lanes = [lane.attrib.get('shape', None) for lane in elem.findall('lane') if lane.attrib.get('shape', None)]
            self.edges[edge_id] = {'from': from_node, 'to': to_node, 'lanes': lanes}

    def _parse_junction(self, elem: ET.Element):
        junction_id = elem.attrib['id']
        inc_lanes = elem.attrib.get('incLanes', '').split()
        self.junctions[junction_id] = {
            'x': float(elem.attrib['x']),
            'y': float(elem.attrib['y']),
            'incLanes': inc_lanes
        }

    def _parse_connection(self, elem: ET.Element):
        from_edge = elem.get('from')
        to_edge = elem.get('to')
        dir = elem.get('dir').lower() if elem.get('dir') in ['R', 'L'] else elem.get('dir')

        if dir not in ['t', 'invalid']:
            if from_edge not in self.connections:
                self.connections[from_edge] = [(to_edge, dir)]
            else:
                existing_connections = [conn[0] for conn in self.connections[from_edge]]
                if to_edge not in existing_connections:
                    self.connections[from_edge].append((to_edge, dir))

    def _parse_tllogic(self, elem: ET.Element):
        tl_id = elem.attrib['id']
        phases = elem.findall('phase')
        for phase in phases:
            duration = phase.attrib['duration']
            state = phase.attrib['state']
            self.tl_logic[tl_id].append({'duration': duration, 'state': state})
