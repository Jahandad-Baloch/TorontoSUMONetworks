import sumolib
import math
from collections import defaultdict

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
        self.net = sumolib.net.readNet(self.network_file)

        net_edges = self.net.getEdges(withInternal=False)
        net_junctions = self.net.getNodes()
        net_tls = self.net.getTrafficLights()

        for edge in net_edges:
            self._parse_edge(edge)

        for junction in net_junctions:
            self._parse_junction(junction)

        for tls in net_tls:
            self._parse_tllogic(tls)
        
        if self.logger:
            self.logger.info(f"Loaded SUMO network elements from: {self.network_file}")

    def _parse_edge(self, edge) -> None:
        """Parse edge and its connections."""
        lanes = [
            {
                'id': str(lane.getID()),
                'shape': [(float(x), float(y)) for x, y in lane.getShape()],
                'length': float(lane.getLength()),
                'speed': float(lane.getSpeed()),
                'width': float(lane.getWidth())
            }
            for lane in edge.getLanes()
        ]
        connections = []
        for to_edge in edge.getOutgoing():
            edge_connections = edge.getConnections(to_edge)
            for connection in edge_connections:
                from_node = edge.getFromNode()
                to_node = edge.getToNode()
                direction_vector = self._calculate_direction_vector(from_node, to_node)
                cardinal_direction = self._assign_cardinal_direction(direction_vector)
                connections.append({
                    'from_lane': str(connection.getFromLane().getID()),
                    'to_lane': str(connection.getToLane().getID()),
                    'via': str(connection.getViaLaneID()),
                    'tl': str(connection.getTLSID()),
                    'link_index': connection.getTLLinkIndex(),
                    'dir': connection.getDirection(),
                    'direction_vector': tuple(round(coord, 4) for coord in direction_vector),
                    'cardinal_direction': cardinal_direction,
                    'state': connection.getState()
                })
        self.edges[str(edge.getID())] = {
            'from': str(edge.getFromNode().getID()),
            'to': str(edge.getToNode().getID()),
            'lanes': lanes,
            'connections': connections
        }

    def _parse_tllogic(self, tls) -> None:
        """Parse traffic light logic."""
        tl_id = tls.getID()
        for program in tls.getPrograms():
            for phase in program.getPhases():
                self.tl_logic[tl_id].append({'duration': phase.duration, 'state': phase.state})


    def _parse_junction(self, junction) -> None:
        """Parse junction information."""
        inc_edges = junction.getIncoming()
        inc_lanes = [str(lane.getID()) for lane in inc_edges]
        edge_ids = '|'.join(str(edge.getID()) for edge in inc_edges)
        
        # Get directions as a list
        directions_list = [
            self._assign_cardinal_direction(
                self._calculate_direction_vector(edge.getFromNode(), edge.getToNode())
            ) 
            for edge in inc_edges
        ]
        
        # Join directions into a pipe-separated string for consistency with edge_ids
        directions_str = '|'.join(directions_list)
        
        self.junctions[str(junction.getID())] = {
            'x': float(junction.getCoord()[0]),
            'y': float(junction.getCoord()[1]),
            'incLanes': inc_lanes,
            'edge_ids': edge_ids,
            'directions': directions_str  # Now a string, not a list
        }

    def _calculate_direction_vector(self, from_node, to_node) -> tuple:
        """Calculate vector from one node to another."""
        from_x, from_y = from_node.getCoord()
        to_x, to_y = to_node.getCoord()
        return (to_x - from_x, to_y - from_y)

    def _assign_cardinal_direction(self, direction_vector: tuple) -> str:
        """Assign cardinal direction based on the dataset-defined approach categories."""
        dx, dy = direction_vector
        angle_degrees = math.degrees(math.atan2(dy, dx)) % 360
        if 0 <= angle_degrees < 45 or 315 <= angle_degrees < 360:
            return 'e_appr'
        elif 45 <= angle_degrees < 135:
            return 'n_appr'
        elif 135 <= angle_degrees < 225:
            return 'w_appr'
        elif 225 <= angle_degrees < 315:
            return 's_appr'
        else:
            return self._closer_cardinal_direction(angle_degrees)

    def _closer_cardinal_direction(self, angle: float) -> str:
        """Return closest cardinal direction based on angle."""
        directions = {0: 'e_appr', 90: 'n_appr', 180: 'w_appr', 270: 's_appr'}
        closest = min(directions.keys(), key=lambda k: min(abs(angle - k), 360 - abs(angle - k)))
        return directions[closest]
