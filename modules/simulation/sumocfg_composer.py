# modules/simulation/sumocfg_composer.py
import xml.etree.ElementTree as ET
from xml.dom import minidom
from modules.core.simulation_task import SimulationTask
from modules.core.network_base import NetworkBase

""" 
This script is used to compose the SUMO configuration file.
path: scripts/simulation/sumocfg_composer.py
"""

class SumoConfigComposer(NetworkBase, SimulationTask):
    """Composes the SUMO configuration file.

    Args:
        app_context (AppContext): Central application context.
    """
    def __init__(self, app_context) -> None:
        """
        Initializes the SumoConfigComposer object.
        Args:
            app_context (AppContext): Central application context.
        """
        super().__init__(app_context)

    def compose_sumo_config(self) -> None:
        """Composes the SUMO configuration XML file based on the network settings."""
        root = ET.Element("configuration")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.set("xsi:noNamespaceSchemaLocation", "http://sumo.dlr.de/xsd/sumoConfiguration.xsd")

        input_elem = ET.SubElement(root, "input")
        net_file = ET.SubElement(input_elem, "net-file")
        net_file.set("value", f"{self.network_name}_{self.network_type}.net.xml")

        route_files_list = []
        additional_files_list = []

        for mode in self.modes:
            route_files_list.append(f"{self.network_name}_{mode}_routes.rou.xml")
            additional_files_list.append(f"{self.network_name}_{mode}_vtype.rou.xml")

        if self.simulation_settings['simulate_public_transport']:
            route_files_list.append(f"{self.network_name}_public_transport.rou.xml")
            additional_files_list.extend([
                f"{self.network_name}_public_transport_vtype.rou.xml",
                f"{self.network_name}_gtfs_stops_routes.add.xml"
            ])

        if self.simulation_settings['add_induction_loops']:
            additional_files_list.append("e1_detectors.add.xml")
        if self.simulation_settings['add_lanearea_detectors']:
            additional_files_list.append("e2_detectors.add.xml")

        route_files = ET.SubElement(input_elem, "route-files")
        route_files.set("value", ", ".join(route_files_list))
        additional_files = ET.SubElement(input_elem, "additional-files")
        additional_files.set("value", ", ".join(additional_files_list))

        time_elem = ET.SubElement(root, "time")
        begin = ET.SubElement(time_elem, "begin")
        begin.set("value", str(self.simulation_settings['begin']))
        end = ET.SubElement(time_elem, "end")
        end.set("value", str(self.simulation_settings['end']))

        report_elem = ET.SubElement(root, "report")
        no_warnings = ET.SubElement(report_elem, "no-warnings")
        no_warnings.set("value", str(self.simulation_settings['no_warnings']))

        self.save_xml_file(root, self.sumo_cfg_file)

    def save_xml_file(self, root: ET.Element, file_path: str) -> None:
        """Saves the XML tree to file.

        Args:
            root (ET.Element): Root element of the XML.
            file_path (str): Destination file path.
        """
        with open(file_path, "w") as f:
            f.write(self.prettify(root))
        self.logger.info(f"XML configuration saved to {file_path}")
        self.logger.info(f"\n.......................\n")

    def prettify(self, elem: ET.Element) -> str:
        """Returns a pretty-printed XML string.

        Args:
            elem (ET.Element): XML element.

        Returns:
            str: Formatted XML string.
        """
        rough_string = ET.tostring(elem, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def execute(self) -> None:
        """Task entry-point: composes the SUMO configuration file."""
        self.compose_sumo_config()