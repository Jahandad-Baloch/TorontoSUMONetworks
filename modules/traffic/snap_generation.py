# modules/traffic/snap_generation.py
# Description: This script is used to generate snaps for the network.

import os
from modules.core.network_base import NetworkBase
from modules.network.network_parser import NetworkParser
from matplotlib import pyplot as plt

class SnapGenerator(NetworkBase):
    """Generates network snapshots using matplotlib.

    Args:
        config_file (str): Path to configuration file.
    """
    def __init__(self, config_file: str) -> None:
        """
        Initialize the snap generator.

        Args:
            config_path (str): Path to the configuration file.
        """
        super().__init__(config_file)
        self.network_parser = NetworkParser(self.net_file, self.logger)

    def generate_snaps(self) -> None:
        """Generate and display/save network snapshots."""
        self.network_parser.load_network()
        self.edge_data = self.network_parser.edges
        self.plot_network()

    def plot_network(self) -> None:
        """Plot network based on node and edge data."""
        nodes = self.network_parser.junctions
        edges = self.network_parser.edges
        plt.figure(figsize=(10, 10))
        for edge_id, edge_data in edges.items():
            from_node = nodes[edge_data['from']]
            to_node = nodes[edge_data['to']]
            plt.plot([from_node['x'], to_node['x']], [from_node['y'], to_node['y']], 'b-')
        if self.config['execution_settings']['show_snaps']:
            plt.show()
        if self.config['execution_settings']['save_snaps']:
            plt.savefig(os.path.join(self.network_outputs, "network_snap.png"))
            plt.close()
            
    # For generating a rich network visualization, without using SUMO tools, we can use the, 
    # more data such as lane width, lane length, lane shape, etc. to generate a more detailed network visualization.
    # matplotlib library and more advanced visualization techniques.
    # Idea of generating a rich network visualization:
    # 1. Use the network parser to extract the network data.
    # 2. The network data includes information about the edges, their lanes, and the junctions with their attributes.
    # 3. Advanced visualization techniques in matplotlib:
    #    - Plot the network graph with nodes and edges.
    #    - Use different colors and line styles for different types of roads.
    #    - Add labels to the nodes and edges.
    #    - Add legends and annotations to the plot.
    #    - Customize the plot appearance with titles, axis labels, and grid lines.
    # 4. Save the visualization as an image or interactive plot.
    # 5. Display the visualization in a GUI window or web application.
    
    """ 
    
                lanes
                ({
                'id': str,
                'shape': [(float(x), float(y))
                'length': float
                'speed': float
                'width': float
                })
                connections
                ({
                    'from_lane': from_lane,
                    'to_lane': to_lane,
                    'via': via,
                    'tl': tl,
                    'link_index': link_index,
                    'dir': turn_dir,
                    'direction_vector': direction_vector,
                    'cardinal_direction': cardinal_direction,
                    'state': state
                })

        # edge data along with parsed lanes and connections
        self.edges
        {
            'from': str(From Node)
            'to': str(To Node)
            'lanes': lanes,
            'connections': connections  # connections within edges
        }
        self.junctions[str(junction.getID())] = {
            'x': float(Coord)
            'y': float(Coord)
            'incLanes': 
            'edge_ids': 
        }
    """
    
    def advanced_plot_network(self) -> None:
        """Plot network with advanced visualization."""
        nodes = self.network_parser.junctions
        edges = self.network_parser.edges
        plt.figure(figsize=(10, 10))
        for edge_data in edges.values():
            from_node = nodes[edge_data['from']]
            to_node = nodes[edge_data['to']]
            for lane in edge_data['lanes']:
                lane_x, lane_y = zip(*lane['shape'])
                plt.plot(lane_x, lane_y, 'b-')
        if self.config['execution_settings']['show_snaps']:
            plt.show()
        if self.config['execution_settings']['save_snaps']:
            plt.close()
    
    
    
            
# Test the SnapGenerator
if __name__ == "__main__":
    config_file = "configurations/main_config.yaml"
    snap_generator = SnapGenerator(config_file)
    snap_generator.generate_snaps()
    print("Snap generation completed.")
