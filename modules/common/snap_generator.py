# modules/common/snap_generator.py
from __future__ import annotations
import os
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from modules.core.simulation_task import SimulationTask
from modules.network.network_parser import NetworkParser
from modules.common.command_executor import CommandExecutor

class SnapGenerator(SimulationTask):
    """Generates snapshot images of the SUMO network using optimized vectorized plotting.

    This task loads the network and produces snapshot images based on configuration settings.
    Snapshots can be displayed or saved to file.
    """

    def __init__(self, app_context) -> None:
        """
        Initializes the SnapGenerator task.

        Args:
            app_context (AppContext): Shared application context containing configuration and logger.
        """
        super().__init__(app_context)
        self.config = self.app_context.config
        self.paths = self.config['paths']
        # Determine network name based on network configuration.
        network_config = self.config['network']
        network_extent = network_config['extent']
        if network_extent == 'by_junctions':
            self.network_name = network_config['area'][network_extent]['name'].replace(' ', '_').lower()
        else:
            self.network_name = network_config['area'][network_extent].replace(' ', '_').lower()
        self.network_outputs = os.path.join(self.paths['network_data'], self.network_name)
        self.net_file = os.path.join(self.network_outputs, f"{self.network_name}_{network_config['type']}.net.xml")
        self.network_parser = NetworkParser(self.net_file, self.logger)
        self.executor = CommandExecutor(logger=self.logger)

    def execute(self) -> None:
        """
        Executes the snapshot generation task.
        """
        self.logger.info("Starting snapshot generation task.")
        self.network_parser.load_network()
        self.plot_network()

    def plot_network(self) -> None:
        """
        Generates a network snapshot using an optimized vectorized approach.

        This method gathers all edge segments into a single LineCollection, which is then
        drawn in one call. This approach is significantly faster than plotting each edge individually.
        """
        self.logger.info("Plotting network snapshot using LineCollection.")
        # Retrieve junction (node) and edge data from the network parser.
        junctions = self.network_parser.junctions
        edges = self.network_parser.edges

        segments = []
        # Instead of plotting every lane separately, we use junctions to form segments.
        for edge in edges.values():
            from_node = junctions.get(edge['from'])
            to_node = junctions.get(edge['to'])
            if from_node and to_node:
                segments.append([(from_node['x'], from_node['y']),
                                 (to_node['x'], to_node['y'])])

        # Create a LineCollection from all segments.
        lc = LineCollection(segments, colors='blue', linewidths=0.5)

        fig, ax = plt.subplots(figsize=(10, 10))
        ax.add_collection(lc)
        # Optionally, plot junctions as red dots.
        if junctions:
            xs = [node['x'] for node in junctions.values()]
            ys = [node['y'] for node in junctions.values()]
            ax.scatter(xs, ys, c='red', s=10)
        ax.autoscale_view()
        ax.set_aspect('equal', 'box')

        # execution_settings = self.config.get('execution_settings', {})
        # if execution_settings.get('show_snaps', False):
        #     plt.show()
        
        snap_path = os.path.join(self.network_outputs, "network_snaps.png")        
        plt.savefig(snap_path, dpi=150)
        self.logger.info(f"Snapshot saved to {snap_path}.")

        plt.close()
        self.logger.info("Snapshot generation completed.")


    def generate_sumo_snaps(self) -> None:
        """
        Generates snapshots using SUMO tools.
        """
        self.logger.info("Generating snapshots using SUMO tools.")
        network_outputs = self.config['paths'].get('network_data', '')
        net_file = str(self.config['paths'].get('net_file', ''))
        output_file = os.path.join(network_outputs, "network_snaps.xml")
        # tool_snaps = os.path.join(self.config['paths'].get('sumo_tools', ''), "output", "generateNetworkSnaps.py")
        tool_snaps = os.path.join(self.sumo_tools_path, "output", "generateNetworkSnaps.py")
        command = [
            "python", tool_snaps,
            "-n", net_file,
            "-o", output_file
        ]
        self.executor.run_command(command)

    # def plot_network(self) -> None:
    #     """
    #     Generates a network snapshot using matplotlib.
    #     """
    #     self.logger.info("Plotting network snapshot using matplotlib.")
    #     nodes = self.network_parser.junctions
    #     edges = self.network_parser.edges

    #     plt.figure(figsize=(10, 10))
    #     for edge_id, edge_data in edges.items():
    #         from_node = nodes.get(edge_data['from'])
    #         to_node = nodes.get(edge_data['to'])
    #         if from_node and to_node:
    #             plt.plot([from_node['x'], to_node['x']],
    #                      [from_node['y'], to_node['y']], 'b-')
    #     execution_settings = self.config.get('execution_settings', {})
    #     if execution_settings.get('show_snaps', False):
    #         plt.show()
    #     if execution_settings.get('save_snaps', False):
    #         network_outputs = self.config['paths'].get('network_data', '')
    #         snap_path = os.path.join(network_outputs, "network_snaps.png")
    #         plt.savefig(snap_path)
    #         plt.close()
    #         self.logger.info(f"Snapshot saved to {snap_path}.")
    #     self.logger.info("Snapshot generation completed.")
