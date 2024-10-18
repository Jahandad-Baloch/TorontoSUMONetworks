import os
import xml.etree.ElementTree as ET
from xml.dom import minidom

""" 
This script defines the edge types for the SUMO network.
path: scripts/common/edge_types_xml.py
"""

class EdgeTypesXML:
    """
    Class to generate edge types XML for the SUMO network.
    """
    """ 
    gdf['FEATURE_CODE'].unique():  [201500 201200 203001 207001 206001 201400 201300 202001 201100 201700
    201101 201800 201201 201600 205001 204002 206002 202002 204001 203002
    201401 201801 208001 201803 201601 201301]
    gdf['FEATURE_CODE_DESC'].unique():  ['Local' 'Major Arterial' 'River' 'Geostatistical line' 'Major Shoreline'
    'Collector' 'Minor Arterial' 'Major Railway' 'Expressway' 'Laneway'
    'Expressway Ramp' 'Pending' 'Major Arterial Ramp' 'Other' 'Hydro Line'
    'Walkway' 'Minor Shoreline (Land locked)' 'Minor Railway' 'Trail'
    'Creek/Tributary' 'Collector Ramp' 'Busway' 'Ferry Route' 'Access Road'
    'Other Ramp' 'Minor Arterial Ramp']
    """

    type_mappings2 = {
        'arterial': {
            201100: {'id': '201100', 'oneway': 'true', 'name': 'Expressway', 'allow': 'passenger taxi delivery emergency evehicle truck bus coach trailer'},
            201800: {'id': '201800', 'oneway': 'true', 'name': 'Expressway Ramp', 'allow': 'passenger taxi delivery emergency evehicle truck bus coach trailer'},
            201200: {'id': '201200', 'oneway': 'true', 'name': 'Major Arterial', 'allow': 'passenger taxi delivery emergency evehicle truck bus coach trailer'},
            201300: {'id': '201300', 'oneway': 'true', 'name': 'Minor Arterial', 'allow': 'passenger taxi delivery emergency evehicle truck bus coach trailer'},
            201600: {'id': '201600', 'oneway': 'true', 'name': 'Major Arterial Ramp', 'allow': 'passenger taxi delivery emergency evehicle truck bus coach trailer'},
            201301: {'id': '201301', 'oneway': 'true', 'name': 'Minor Arterial Ramp', 'allow': 'passenger taxi delivery emergency evehicle truck bus coach trailer'},
            201801: {'id': '201801', 'oneway': 'false', 'name': 'Busway', 'allow': 'passenger taxi delivery emergency evehicle truck bus coach trailer'}
        },
        'collector': {
            201400: {'id': '201400', 'oneway': 'false', 'name': 'Collector', 'allow': 'passenger taxi delivery emergency evehicle truck bus coach trailer'},
            201401: {'id': '201401', 'oneway': 'true', 'name': 'Collector Ramp', 'allow': 'passenger taxi delivery emergency evehicle truck bus coach trailer'},
            201803: {'id': '201803', 'oneway': 'false', 'name': 'Access Road', 'allow': 'passenger taxi delivery emergency evehicle truck bus coach trailer pedestrian bicycle moped motorcycle scooter'},
            201601: {'id': '201601', 'oneway': 'true', 'name': 'Other Ramp', 'allow': 'passenger taxi delivery emergency evehicle truck bus coach trailer'},
        },
        'local': {
            201500: {'id': '201500', 'oneway': 'false', 'name': 'Local', 'allow': 'passenger taxi delivery emergency evehicle truck bus coach trailer'},
            201700: {'id': '201700', 'oneway': 'false', 'name': 'Laneway', 'allow': 'pedestrian bicycle moped motorcycle scooter passenger taxi emergency evehicle'},
            204001: {'id': '204001', 'oneway': 'false', 'name': 'Trail', 'allow': 'pedestrian bicycle moped motorcycle scooter'},
            204002: {'id': '204002', 'oneway': 'false', 'name': 'Walkway', 'allow': 'pedestrian bicycle moped motorcycle scooter'}
        }
    }

    type_mappings = {
        'arterial': {
            201100: {'id': '201100', 'priority': 5, 'numLanes': 4, 'speed': 27.78, 'oneway': 'true', 'name': 'Expressway', 'allow': 'passenger taxi delivery emergency evehicle truck bus coach trailer'},
            201800: {'id': '201800', 'priority': 4, 'numLanes': 1, 'speed': 25.0, 'oneway': 'true', 'name': 'Expressway Ramp', 'allow': 'passenger taxi delivery emergency evehicle truck bus coach trailer'},
            201200: {'id': '201200', 'priority': 4, 'numLanes': 3, 'speed': 12.5, 'oneway': 'true', 'name': 'Major Arterial', 'allow': 'passenger taxi delivery emergency evehicle truck bus coach trailer'},
            201300: {'id': '201300', 'priority': 3, 'numLanes': 2, 'speed': 12.5, 'oneway': 'true', 'name': 'Minor Arterial', 'allow': 'passenger taxi delivery emergency evehicle truck bus coach trailer'},
            201600: {'id': '201600', 'priority': 4, 'numLanes': 1, 'speed': 12.5, 'oneway': 'true', 'name': 'Major Arterial Ramp', 'allow': 'passenger taxi delivery emergency evehicle truck bus coach trailer'},
            201301: {'id': '201301', 'priority': 3, 'numLanes': 1, 'speed': 12.5, 'oneway': 'true', 'name': 'Minor Arterial Ramp', 'allow': 'passenger taxi delivery emergency evehicle truck bus coach trailer'},
            201801: {'id': '201801', 'priority': 2, 'numLanes': 1, 'speed': 11.11, 'oneway': 'false', 'name': 'Busway', 'allow': 'passenger taxi delivery emergency evehicle truck bus coach trailer'}
        },
        'collector': {
            201400: {'id': '201400', 'priority': 3, 'numLanes': 2, 'speed': 12.5, 'oneway': 'false', 'name': 'Collector', 'allow': 'passenger taxi delivery emergency evehicle truck bus coach trailer'},
            201401: {'id': '201401', 'priority': 3, 'numLanes': 1, 'speed': 11.11, 'oneway': 'true', 'name': 'Collector Ramp', 'allow': 'passenger taxi delivery emergency evehicle truck bus coach trailer'},
            201803: {'id': '201803', 'priority': 1, 'numLanes': 1, 'speed': 5.56, 'oneway': 'false', 'name': 'Access Road', 'allow': 'passenger taxi delivery emergency evehicle truck bus coach trailer pedestrian bicycle moped motorcycle scooter'},
            201601: {'id': '201601', 'priority': 4, 'numLanes': 1, 'speed': 12.5, 'oneway': 'true', 'name': 'Other Ramp', 'allow': 'passenger taxi delivery emergency evehicle truck bus coach trailer'},
        },
        'local': {
            201500: {'id': '201500', 'priority': 2, 'numLanes': 2, 'speed': 12.5, 'oneway': 'false', 'name': 'Local', 'allow': 'passenger taxi delivery emergency evehicle truck bus coach trailer'},
            201700: {'id': '201700', 'priority': 1, 'numLanes': 1, 'speed': 4.17, 'oneway': 'false', 'name': 'Laneway', 'allow': 'pedestrian bicycle moped motorcycle scooter passenger taxi emergency evehicle'},
            204001: {'id': '204001', 'priority': 1, 'numLanes': 1, 'speed': 5.56, 'oneway': 'false', 'name': 'Trail', 'allow': 'pedestrian bicycle moped motorcycle scooter'},
            204002: {'id': '204002', 'priority': 1, 'numLanes': 1, 'speed': 5.56, 'oneway': 'false', 'name': 'Walkway', 'allow': 'pedestrian bicycle moped motorcycle scooter'}
        }
    }

    @staticmethod
    def create(network_type, output_file):
        """
        Create an XML representation of edge types from dynamic attributes, reusing arterial lanes.
        Save the XML string to a file.
        Args:
            network_type (str): The type of network (arterial, collector, local).

        Returns:
            dict: type mappings for the network type.
        """
        # Start with arterial types and extend based on the selected network type
        active_mappings = EdgeTypesXML.type_mappings['arterial'].copy()
        
        if network_type == 'collector':
            # Add specific collector lanes
            active_mappings.update(EdgeTypesXML.type_mappings['collector'])
        elif network_type == 'local':
            # Add specific local lanes
            active_mappings.update(EdgeTypesXML.type_mappings['local'])
        
        types = ET.Element("types")
        for feature_code, attributes in active_mappings.items():
            type_element = ET.SubElement(types, "type")
            for attr_key, attr_value in attributes.items():
                type_element.set(attr_key, str(attr_value))

        rough_string = ET.tostring(types, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        xml_str = reparsed.toprettyxml(indent="  ")

        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(xml_str)
        
        return active_mappings

if __name__ == "__main__":
    edge_types_xml = EdgeTypesXML.create('arterial', 'edge_types.xml')
