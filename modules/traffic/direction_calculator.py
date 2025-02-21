# modules/traffic/direction_calculator.py
import math
import pandas as pd

""" 
Description: This script contains the class for calculating the directions of the edges in the network.
"""

class DirectionCalculator:
    """Calculate cardinal directions for network edges.

    Args:
        edges (dict): Dictionary of edge data.
        traffic_settings (dict): Traffic configuration (expects key 'epsilon_value').
        logger: Logger instance.
    """
    def __init__(self, edges: dict, traffic_settings: dict, logger) -> None:
        self.edges = edges
        self.epsilon: float = traffic_settings['epsilon_value']
        self.edge_directions = {}
        self.logger = logger

    def calculate_directions(self) -> pd.DataFrame:
        """Calculate and store cardinal directions for each edge.

        Returns:
            pd.DataFrame: DataFrame mapping edge IDs to directions.
        """
        reverse_direction = {'eb': 'wb', 'wb': 'eb', 'nb': 'sb', 'sb': 'nb'}

        for edge_id, edge_data in self.edges.items():
            directions = []
            for lane in edge_data['lanes']:
                direction = self._calculate_edge_direction(lane)
                directions.append(direction)
            if directions:
                self.edge_directions[edge_id] = max(set(directions), key=directions.count)
                self.edge_directions['-' + edge_id] = reverse_direction[self.edge_directions[edge_id]]
        
        self.logger.info(f"Calculated directions for {len(self.edge_directions)} edges")
        return pd.DataFrame(self.edge_directions.items(), columns=['edge_id', 'direction'])

    def _calculate_edge_direction(self, lane: dict) -> str:
        """Calculate the cardinal direction for a given lane shape.

        Args:
            lane (dict): A dictionary representing lane properties.
            
        Returns:
            str: Cardinal direction.
        """
        points = lane.get('shape', [])
        if not points:
            return 'unknown'
        start_x, start_y = points[0]
        end_x, end_y = points[-1]

        delta_x = end_x - start_x
        delta_y = end_y - start_y
        angle_degrees = math.degrees(math.atan2(delta_y, delta_x))

        return self._assign_cardinal_direction(angle_degrees)

    def _assign_cardinal_direction(self, angle: float) -> str:
        """Determine cardinal direction based on angle.

        Args:
            angle (float): Angle in degrees.
            
        Returns:
            str: Cardinal direction.
        """
        if -self.epsilon <= angle < 45 + self.epsilon or 315 - self.epsilon <= angle < 360:
            return 'eb'
        elif 45 - self.epsilon <= angle < 135 + self.epsilon:
            return 'nb'
        elif 135 - self.epsilon <= angle < 225 + self.epsilon:
            return 'wb'
        elif 225 - self.epsilon <= angle < 315 + self.epsilon:
            return 'sb'
        return self._closer_cardinal_direction(angle)

    def _closer_cardinal_direction(self, angle: float) -> str:
        """Find the closest cardinal direction if none of the intervals match.

        Args:
            angle (float): Angle in degrees.
            
        Returns:
            str: Closest cardinal direction.
        """
        directions = {0: 'eb', 90: 'nb', 180: 'wb', 270: 'sb'}
        closest_cardinal = min(directions.keys(), key=lambda k: min(abs(angle - k), 360 - abs(angle - k)))
        return directions[closest_cardinal]
