import math
import pandas as pd

class DirectionCalculator:
    def __init__(self, edges: dict, traffic_settings: float, logger):
        self.edges = edges
        self.epsilon = traffic_settings['epsilon_value']
        self.edge_directions = {}
        self.logger = logger

    def calculate_directions(self):
        reverse_direction = {'eb': 'wb', 'wb': 'eb', 'nb': 'sb', 'sb': 'nb'}

        for edge_id, edge_data in self.edges.items():
            directions = []
            for shape in edge_data['lanes']:
                direction = self._calculate_edge_direction(shape)
                directions.append(direction)
            if directions:
                self.edge_directions[edge_id] = max(set(directions), key=directions.count)
                self.edge_directions['-' + edge_id] = reverse_direction[self.edge_directions[edge_id]]
        
        self.logger.info(f"Calculated directions for {len(self.edge_directions)} edges")
        return pd.DataFrame(self.edge_directions.items(), columns=['edge_id', 'direction'])

    def _calculate_edge_direction(self, shape: str) -> str:
        points = shape.split()
        start_x, start_y = map(float, points[0].split(','))
        end_x, end_y = map(float, points[-1].split(','))

        delta_x = end_x - start_x
        delta_y = end_y - start_y
        angle_degrees = math.degrees(math.atan2(delta_y, delta_x))

        return self._assign_cardinal_direction(angle_degrees)

    def _assign_cardinal_direction(self, angle: float) -> str:
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
        directions = {0: 'eb', 90: 'nb', 180: 'wb', 270: 'sb'}
        closest_cardinal = min(directions.keys(), key=lambda k: min(abs(angle - k), 360 - abs(angle - k)))
        return directions[closest_cardinal]
