# modules/network/network_parser.py
import sumolib
import math
from collections import defaultdict
from matplotlib import pyplot as plt

class NetworkParser:
    """
    Parses SUMO network files to extract nodes, edges, and traffic light logic.

    Args:
        network_file (str): Path to the network file.
        logger: Logger instance.
    """
    def __init__(self, network_file: str, logger) -> None:
        self.network_file = network_file
        self.logger = logger
        self.edges = {}
        self.junctions = {}
        self.tl_logic = defaultdict(list)

    def load_network(self) -> None:
        """Load the SUMO network and parse elements."""
        self.logger.info(f"Loading SUMO network from: {self.network_file}")
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
        if self.logger:
            self.logger.info(f"Loaded SUMO network elements from: {self.network_file}")

    def _parse_edge(self, edge) -> None:
        """Parse edge and its connections."""
        lanes = []
        for lane in edge.getLanes():
            lanes.append({
                'id': str(lane.getID()),
                'shape': [(float(x), float(y)) for x, y in lane.getShape()],
                'length': float(lane.getLength()),
                'speed': float(lane.getSpeed()),
                'width': float(lane.getWidth())
            })
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
        self.edges[str(edge.getID())] = {
            'from': str(edge.getFromNode().getID()),
            'to': str(edge.getToNode().getID()),
            'lanes': lanes,
            'connections': connections
        }

    def _parse_junction(self, junction) -> None:
        """Parse junction information."""
        inc_edges = junction.getIncoming()
        inc_lanes = [str(lane.getID()) for lane in inc_edges]
        edge_ids = '|'.join(str(edge.getID()) for edge in inc_edges)
        self.junctions[str(junction.getID())] = {
            'x': float(junction.getCoord()[0]),
            'y': float(junction.getCoord()[1]),
            'incLanes': inc_lanes,
            'edge_ids': edge_ids
        }

    def _parse_tllogic(self, tls) -> None:
        """Parse traffic light logic."""
        tl_id = tls.getID()
        for program in tls.getPrograms():
            for phase in program.getPhases():
                self.tl_logic[tl_id].append({'duration': phase.duration, 'state': phase.state})

    def _calculate_direction_vector(self, from_node, to_node) -> tuple:
        """Calculate vector from one node to another."""
        from_x, from_y = from_node.getCoord()
        to_x, to_y = to_node.getCoord()
        return (to_x - from_x, to_y - from_y)

    def _assign_cardinal_direction(self, direction_vector: tuple) -> str:
        """Assign cardinal direction from a vector."""
        dx, dy = direction_vector
        angle_degrees = math.degrees(math.atan2(dy, dx)) % 360
        if 0 <= angle_degrees < 45 or 315 <= angle_degrees < 360:
            return 'eb'
        elif 45 <= angle_degrees < 135:
            return 'nb'
        elif 135 <= angle_degrees < 225:
            return 'wb'
        elif 225 <= angle_degrees < 315:
            return 'sb'
        else:
            return self._closer_cardinal_direction(angle_degrees)

    def _closer_cardinal_direction(self, angle: float) -> str:
        """Return closest cardinal direction based on angle."""
        directions = {0: 'eb', 90: 'nb', 180: 'wb', 270: 'sb'}
        closest = min(directions.keys(), key=lambda k: min(abs(angle - k), 360 - abs(angle - k)))
        return directions[closest]

    def plot_network(self) -> None:
        """Plot network using matplotlib."""
        junction_x = [j['x'] for j in self.junctions.values()]
        junction_y = [j['y'] for j in self.junctions.values()]
        plt.figure(figsize=(10, 10))
        plt.scatter(junction_x, junction_y, c='r', s=10)
        for edge_data in self.edges.values():
            for lane in edge_data['lanes']:
                lane_x, lane_y = zip(*lane['shape'])
                plt.plot(lane_x, lane_y, 'b-')
        plt.savefig("network_snaps.png")
        plt.close()
        self.logger.info("Network plot saved.")