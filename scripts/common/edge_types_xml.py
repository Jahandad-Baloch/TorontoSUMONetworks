# scripts/build_sumo_net/edge_types_definer.py
# This script defines the edge types for the SUMO network.

import os
import xml.etree.ElementTree as ET
from xml.dom import minidom


class EdgeTypesXML:

    type_mappings = {
        204001: {'id': '204001', 'priority': 1, 'numLanes': 1, 'speed': 5.56, 'oneway': 'false', 'name': 'Trail'}, 
        201101: {'id': '201101', 'priority': 4, 'numLanes': 1, 'speed': 25.0, 'oneway': 'true', 'name': 'Expressway Ramp'}, 
        201400: {'id': '201400', 'priority': 3, 'numLanes': 2, 'speed': 12.5, 'oneway': 'false', 'name': 'Collector'}, 
        201500: {'id': '201500', 'priority': 2, 'numLanes': 2, 'speed': 12.5, 'oneway': 'false', 'name': 'Local'}, 
        201100: {'id': '201100', 'priority': 5, 'numLanes': 4, 'speed': 27.78, 'oneway': 'true', 'name': 'Expressway'}, 
        201700: {'id': '201700', 'priority': 1, 'numLanes': 1, 'speed': 4.17, 'oneway': 'false', 'name': 'Laneway'}, 
        201200: {'id': '201200', 'priority': 4, 'numLanes': 4, 'speed': 13.89, 'oneway': 'false', 'name': 'Major Arterial'}, 
        201300: {'id': '201300', 'priority': 3, 'numLanes': 2, 'speed': 12.5, 'oneway': 'false', 'name': 'Minor Arterial'}, 
        201201: {'id': '201201', 'priority': 4, 'numLanes': 1, 'speed': 12.5, 'oneway': 'true', 'name': 'Major Arterial Ramp'}, 
        201803: {'id': '201803', 'priority': 1, 'numLanes': 1, 'speed': 5.56, 'oneway': 'false', 'name': 'Access Road'}, 
        201801: {'id': '201801', 'priority': 2, 'numLanes': 1, 'speed': 11.11, 'oneway': 'false', 'name': 'Busway'},
        201601: {'id': '201601', 'priority': 4, 'numLanes': 1, 'speed': 13.89, 'oneway': 'true', 'name': 'Other Ramp'}, 
        201401: {'id': '201401', 'priority': 3, 'numLanes': 1, 'speed': 11.11, 'oneway': 'true', 'name': 'Collector Ramp'}, 
        201301: {'id': '201301', 'priority': 3, 'numLanes': 1, 'speed': 11.11, 'oneway': 'true', 'name': 'Minor Arterial Ramp'}
    }

    @staticmethod
    def create(active_mappings):
        """
        Create an XML representation of edge types.

        Args:
            type_mappings (dict): Mapping of feature codes to attributes.

        Returns:
            str: XML string representation of edge types.
        """
        
        types = ET.Element("types")
        for feature_code, attributes in active_mappings.items():
            type_element = ET.SubElement(types, "type")
            type_element.set("id", attributes["id"])
            # type_element.set("code", str(feature_code))
            type_element.set("priority", str(attributes["priority"]))
            type_element.set("numLanes", str(attributes["numLanes"]))
            type_element.set("speed", str(attributes["speed"]))
            type_element.set("oneway", str(attributes["oneway"]))
            type_element.set("description", str(attributes["name"]))

        rough_string = ET.tostring(types, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    @staticmethod
    def save(xml_str, output_file):
        """
        Save the XML string to a file.

        Args:
            xml_str (str): XML string.
            output_file (str): Path to the output file.
        """
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(xml_str)

