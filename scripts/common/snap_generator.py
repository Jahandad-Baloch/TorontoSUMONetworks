# Description: This script is used to generate snaps for the network.

# Necessary imports
import os
from scripts.common.network_base import NetworkBase
from scripts.traffic_data_processing.network_parser import NetworkParser
from matplotlib import pyplot as plt

class SnapGenerator(NetworkBase):
    def __init__(self, config_file: str):
        """
        Initialize the snap generator.

        Args:
            config_path (str): Path to the configuration file.
        """
        super().__init__(config_file)
        self.prepare_directories()
        self.network_parser = NetworkParser(self.net_file, self.logger)

    def generate_snaps(self):
        """
        Generate snaps for the network.
        """
        # Load the network using NetworkParser
        self.network_parser.load_network()
        self.edge_data = self.network_parser.edges

        # Generate snaps using matplotlib
        if self.config['execution_settings']['generate_snapshots']:
            self.plot_network()
        # # Generate snaps using SUMO tools
        # if self.config['execution_settings']['snaps_with_sumo']:
        #     self.generate_sumo_snaps()
            
    def generate_sumo_snaps(self):
        """
        Generate snaps for the network using SUMO tools.
        """
        # Generate the network snaps
        output_file = os.path.join(self.network_outputs, "network_snaps.xml")
        tool_snaps = os.path.join(self.sumo_tools_path, "output", "generateNetworkSnaps.py")

        command = [
            "python", tool_snaps,
            "-n", self.net_file,
            "-o", output_file
        ]
        self.executor.run_command(command)

    def plot_network(self):
        """
        Plot the network using matplotlib.
        """
        # Get the network data
        nodes = self.network_parser.nodes
        edges = self.network_parser.edges

        # Plot the network
        plt.figure(figsize=(10, 10))
        for edge_id, edge_data in edges.items():
            from_node = nodes[edge_data['from']]
            to_node = nodes[edge_data['to']]
            plt.plot([from_node['x'], to_node['x']], [from_node['y'], to_node['y']], 'b-')
        if self.config['execution_settings']['show_snaps']:
            plt.show()
        if self.config['execution_settings']['save_snaps']:
            plt.savefig(os.path.join(self.network_outputs, "network_snaps.png"))
            # After saving the plot, close the plot
            plt.close()
            
# Test the SnapGenerator
if __name__ == "__main__":
    config_file = "configurations/main_config.yaml"
    snap_generator = SnapGenerator(config_file)
    snap_generator.generate_snaps()
    print("Snap generation completed.")
        