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

  def compose_sumo_config(self):
      """
      Compose the SUMO configuration file based on the network directory, name and settings.
      Incorporate multiple vehicle modes in the configuration.
      """
      root = ET.Element("configuration")
      root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
      root.set("xsi:noNamespaceSchemaLocation", "http://sumo.dlr.de/xsd/sumoConfiguration.xsd")

      input_elem = ET.SubElement(root, "input")
      net_file = ET.SubElement(input_elem, "net-file")
      net_file.set("value", f"{self.network_name}_{self.network_type}.net.xml")

      route_files_list = []
      additional_files_list = []

      # Include route and vehicle type files for each mode
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

  simulate_public_transport: true # for buses
  use_gui: false
  begin: 28800 # 8:00 AM
  end: 34200  # 9:30 AM
  add_induction_loops: true
  add_lanearea_detectors: true
  add_multi_entry_exit_detectors: false
  no_warnings: false
  save_output: true
  summary_output: true
  emission_output: true # emission values of all vehicles for every simulation step
  full_output: false # various information for all edges, lanes and vehicles (good for visualization purposes)
  queue_output: true # lane-based calculation of the actual tailback in front of a junction
  duration_log: true

Output:

<?xml version="1.0" ?>
<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/sumoConfiguration.xsd">
  <input>
    <net-file value="brookhaven-amesbury_arterial.net.xml"/>
    <route-files value="brookhaven-amesbury_routes.rou.xml, brookhaven-amesbury_public_transport.rou.xml"/>
    <additional-files value="brookhaven-amesbury_vtype.rou.xml, brookhaven-amesbury_public_transport_vtype.rou.xml, brookhaven-amesbury_gtfs_stops_routes.add.xml, e1_detectors.add.xml"/>
  </input>
  <time>
    <begin value="28800"/>
    <end value="34200"/>
  </time>
  <report>
    <no-warnings value="False"/>
    <duration-log.statistics value="True"/>
  </report>
</configuration>


"""