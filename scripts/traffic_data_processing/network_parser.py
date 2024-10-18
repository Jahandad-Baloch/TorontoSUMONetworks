import sumolib
import math
from collections import defaultdict
from matplotlib import pyplot as plt

class NetworkParser:
    def __init__(self, network_file: str, logger):
        self.network_file = network_file
        self.logger = logger
        self.edges = {}
        self.junctions = {}
        self.tl_logic = defaultdict(list)

    def load_network(self):
        self.logger.info("Executing NetworkParser.load_network()")

        # Load the network using sumolib
        self.net = sumolib.net.readNet(self.network_file)

        # Parse edges, junctions, and traffic light logic
        net_edges = self.net.getEdges(withInternal=False)
        net_junctions = self.net.getNodes()
        net_tls = self.net.getTrafficLights()

        for edge in net_edges:
            self._parse_edge(edge)

        for junction in net_junctions:
            self._parse_junction(junction)

        for tls in net_tls:
            self._parse_tllogic(tls) # check this method later
        
        # self.plot_network()

        self.logger.info(f"Loaded SUMO network elements from: {self.network_file}")

    # updated parse edge to convert data types into consistent data types
    def _parse_edge(self, edge):
        """Parse edge data and its connections using sumolib methods."""
        # Parse lanes for the edge
        lanes = []
        for lane in edge.getLanes():
            lanes.append({
                'id': str(lane.getID()),
                'shape': [(float(x), float(y)) for x, y in lane.getShape()],
                'length': float(lane.getLength()),
                'speed': float(lane.getSpeed()),
                'width': float(lane.getWidth())
            })

        # Parse connections for the edge
        connections = []
        for to_edge in edge.getOutgoing():
            edge_connections = edge.getConnections(to_edge)
            for connection in edge_connections:
                from_lane = str(connection.getFromLane().getID())
                to_lane = str(connection.getToLane().getID())
                via = str(connection.getViaLaneID())
                tl = str(connection.getTLSID())
                turn_dir = connection.getDirection()
                link_index = connection.getTLLinkIndex()
                state = connection.getState()

                # Manually calculate direction vector using fromNode and toNode coordinates
                from_node = edge.getFromNode()
                to_node = edge.getToNode()
                direction_vector = self._calculate_direction_vector(from_node, to_node)
                cardinal_direction = self._assign_cardinal_direction(direction_vector)
                direction_vector = tuple(round(coord, 4) for coord in direction_vector)

                connections.append({
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

        # Store edge data along with parsed lanes and connections
        self.edges[str(edge.getID())] = {
            'from': str(edge.getFromNode().getID()),
            'to': str(edge.getToNode().getID()),
            'lanes': lanes,
            'connections': connections  # Store connections within edges
        }


    # updated parse junction to convert data types into consistent data types
    def _parse_junction(self, junction):
        """Parse junction data using sumolib methods."""
        inc_edges = junction.getIncoming()
        inc_lanes = [str(lane.getID()) for lane in inc_edges]
        edge_ids = '|'.join(str(edge.getID()) for edge in inc_edges)

        self.junctions[str(junction.getID())] = {
            'x': float(junction.getCoord()[0]),
            'y': float(junction.getCoord()[1]),
            'incLanes': inc_lanes,
            'edge_ids': edge_ids
        }

    def _parse_tllogic(self, tls):
        """Parse Traffic Light System (TLS) and its phases using sumolib methods."""
        tl_id = tls.getID()
        for program in tls.getPrograms():
            for phase in program.getPhases():
                duration = phase.duration
                state = phase.state
                self.tl_logic[tl_id].append({'duration': duration, 'state': state})


    def _calculate_direction_vector(self, from_node, to_node):
        """Calculate the direction vector based on the coordinates of the fromNode and toNode."""
        from_x, from_y = from_node.getCoord()
        to_x, to_y = to_node.getCoord()

        # Calculate the vector difference
        direction_vector = (to_x - from_x, to_y - from_y)

        return direction_vector

    def _assign_cardinal_direction(self, direction_vector):
        """Assign cardinal direction based on the direction vector."""
        dx, dy = direction_vector
        angle_degrees = math.degrees(math.atan2(dy, dx)) % 360

        if 0 <= angle_degrees < 45 or 315 <= angle_degrees < 360:
            return 'eb'  # Eastbound
        elif 45 <= angle_degrees < 135:
            return 'nb'  # Northbound
        elif 135 <= angle_degrees < 225:
            return 'wb'  # Westbound
        elif 225 <= angle_degrees < 315:
            return 'sb'  # Southbound
        else:
            return self._closer_cardinal_direction(angle_degrees)

    def _closer_cardinal_direction(self, angle: float) -> str:
        directions = {0: 'eb', 90: 'nb', 180: 'wb', 270: 'sb'}
        closest_cardinal = min(directions.keys(), key=lambda k: min(abs(angle - k), 360 - abs(angle - k)))
        return directions[closest_cardinal]

    def plot_network(self):
        """
        Plot the network using matplotlib.
        """
        # Plot the network
        
        junction_x = [junction_data['x'] for junction_data in self.junctions.values()]
        junction_y = [junction_data['y'] for junction_data in self.junctions.values()]
        
        plt.figure(figsize=(10, 10))
        plt.scatter(junction_x, junction_y, c='r', s=10) # Plot junctions in red

        for edge_id, edge_data in self.edges.items():

            for lane in edge_data['lanes']:
                lane_shape = lane['shape']
                lane_x, lane_y = zip(*lane_shape)
                plt.plot(lane_x, lane_y, 'b-')

        plt.show()
        plt.savefig("network_snaps.png")
        plt.close()

        self.logger.info("Network plot saved.")