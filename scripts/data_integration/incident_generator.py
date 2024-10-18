import random
import traci
from sumolib import checkBinary
import xml.etree.ElementTree as ET
from scripts.common.utils import ConfigLoader, LoggerSetup, FileIO


""" 
Description: This script generates traffic incidents in the simulation to test the robustness of the traffic simulation model.
path: scripts/data_integration/incident_generator.py
"""

class EventSimulator:
    def __init__(self, config_path):
        """
        Initialize the Event Simulator with predefined incident probabilities.

        Args:
            incident_probabilities (dict): Dictionary of incident types and their probabilities.
        """
        self.config = ConfigLoader.load_config(config_path)

    def generate_incident(self, incident_probabilities):
        """
        Generate a random incident based on predefined probabilities.

        Returns:
            str: Type of incident generated.
        """
        incidents = list(incident_probabilities.keys())
        probabilities = list(incident_probabilities.values())
        incident_type = random.choices(incidents, probabilities)[0]
        return incident_type

    def inject_incident(self, incident_type, edge_id):
        """
        Inject a traffic incident into the simulation.

        Args:
            incident_type (str): Type of incident to inject.
            edge_id (str): Edge ID where the incident occurs.
        """
        if incident_type == 'accident':
            traci.edge.addProgramLogic(edge_id, 'accident')
        elif incident_type == 'stalled_vehicle':
            traci.edge.addProgramLogic(edge_id, 'stalled_vehicle')
        else:
            print(f"Unknown incident type: {incident_type}")


    def simulate_event(self, event_probabilities):
        """
        Simulate an event that affects traffic flow based on predefined probabilities.

        Returns:
            str: Type of event simulated.
        """
        events = list(event_probabilities.keys())
        probabilities = list(event_probabilities.values())
        event_type = random.choices(events, probabilities)[0]
        return event_type

    def adjust_demand(self, demand_file, event_type, event_intensity):
        """
        Adjust the traffic demand file to simulate increased traffic volume during events.

        Args:
            event_type (str): Type of event to simulate.
            event_intensity (float): Intensity of the event affecting traffic flow.
        """
        tree = ET.parse(demand_file)
        root = tree.getroot()

        for vehicle in root.findall('vehicle'):
            arrival_time = float(vehicle.get('arrival'))
            if event_type == 'concert':
                # Increase traffic demand during a concert event
                vehicle.set('arrival', str(arrival_time + event_intensity))
            elif event_type == 'sports_game':
                # Increase traffic demand during a sports game event
                vehicle.set('arrival', str(arrival_time + event_intensity))
            else:
                print(f"Unknown event type: {event_type}")

        tree.write(demand_file)


