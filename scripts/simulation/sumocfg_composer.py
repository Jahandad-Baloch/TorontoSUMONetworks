import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from scripts.common.network_base import NetworkBase

""" 
This script is used to compose the SUMO configuration file.
path: scripts/simulation/sumocfg_composer.py
"""

class SumoConfigComposer(NetworkBase):
    def __init__(self, config_file: str):
      """
      Initializes the SumoConfigComposer object.
      Args:
          config_file (str): Path to the configuration file.
      """

      super().__init__(config_file)
      self.prepare_directories()

    def compose_sumo_config(self):
        """
        Compose the SUMO configuration file based on the network directory, name and settings.
        """
        root = ET.Element("configuration")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.set("xsi:noNamespaceSchemaLocation", "http://sumo.dlr.de/xsd/sumoConfiguration.xsd")

        input_elem = ET.SubElement(root, "input")
        net_file = ET.SubElement(input_elem, "net-file")
        net_file.set("value", f"{self.network_name}_{self.network_type}.net.xml")

        route_files_list = [f"{self.network_name}_routes.rou.xml"]
        additional_files_list = [f"{self.network_name}_vtype.rou.xml"]

        if self.simulation_settings['simulate_public_transport']:
            route_files_list.append(f"{self.network_name}_public_transport.rou.xml")
            additional_files_list.append(f"{self.network_name}_public_transport_vtype.rou.xml")
            additional_files_list.append(f"{self.network_name}_gtfs_stops_routes.add.xml")
        if self.simulation_settings['add_induction_loops']:
            additional_files_list.append("e1_detectors.add.xml")
        if self.simulation_settings['add_lanearea_detectors']:
            additional_files_list.append("e2_detectors.add.xml")
        if self.simulation_settings['add_multi_entry_exit_detectors']:
            additional_files_list.append("e3_detectors.add.xml")


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
        duration_log = ET.SubElement(report_elem, "duration-log.statistics")
        duration_log.set("value", str(self.simulation_settings['duration_log']))

        self.save_xml_file(root, self.sumo_cfg_file)

    def save_xml_file(self, root: ET.Element, file_path: str):
        with open(file_path, "w") as f:
            f.write(self.prettify(root))
        self.logger.info(f"XML traffic movements data has been saved to {file_path}")
        self.logger.info(f"\n.......................\n")

    def prettify(self, elem: ET.Element) -> str:
        rough_string = ET.tostring(elem, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")


if __name__ == "__main__":
    composer = SumoConfigComposer('configurations/main_config.yaml')
    composer.compose_sumo_config()
    
    

""" 
simulation_settings:
    begin: 28800
    end: 34200
    use_gui: False
    summary_output: simulation_summary2.xml
    statistic_output: simulation_stats2.xml
    no_warnings: False
    duration_log: True
    simulate_public_transport: False
    save_output: True

"""

""" 
Output:

<?xml version="1.0" ?>
<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/sumoConfiguration.xsd">
  <input>
    <net-file value="don_valley_west_arterial.net.xml"/>
    <route-files value="don_valley_west_routes.rou.xml"/>
    <additional-files value="don_valley_west_vtype.xml"/>
    <route-files value="don_valley_west_public_transport.rou.xml"/>
    <additional-files value="don_valley_west_public_transport.vtype.xml"/>
    <additional-files value="don_valley_west_gtfs_stops_routes.add.xml"/>
  </input>
  <time>
    <begin value="28800"/>
    <end value="34200"/>
  </time>
  <output>
    <summary-output value="simulation_summary2.xml"/>
    <statistic-output value="simulation_stats2.xml"/>
  </output>
  <report>
    <no-warnings value="False"/>
    <duration-log.statistics value="True"/>
  </report>
</configuration>

"""