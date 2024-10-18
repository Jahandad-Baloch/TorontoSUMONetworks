import sumolib
import libsumo
import traci
import os
import sys
import random
from traffic_light_controller import TrafficLightController
import torch

"""
Methodology to Simulate Accidents in SUMO Traffic Simulation

To simulate accidents in SUMO, we can manipulate vehicle parameters during the simulation to create unsafe driving conditions that lead to collisions. Based on the SUMO documentation, accidents can be caused by:

Overriding safe speeds: Forcing vehicles to travel at unsafe speeds can lead to collisions.
Disabling safety checks: Using traci.vehicle.setSpeedMode and traci.vehicle.setLaneChangeMode to disable safety constraints.
Adjusting driver behavior parameters: Modifying parameters like tau, apparentDecel, or introducing driver imperfections can increase the likelihood of collisions.
Unsafe lane changes: Forcing vehicles to change lanes unsafely by adjusting lcAssertive, lcImpatience, or lcPushy.
Integration with SUMOTrafficSimulator Class

We will integrate accident simulation into the SUMOTrafficSimulator class by:

Adding collision configuration to the SUMO command: Configure how collisions are handled in the simulation.
Implementing accident triggers: Define when and how accidents are triggered during the simulation.
Manipulating vehicle parameters: Adjust vehicle attributes to cause collisions deliberately.

Implementation Idea 1:
1. Add collision configuration to the SUMO command:
    Add the --collision.check-junctions flag to the SUMO command to enable junction collision checks.
    Add the --collision.action flag to specify the action to take when a collision occurs (e.g., none, warn, or stop).
2. Implement accident triggers:
    Define a method to check for accident triggers based on specific conditions (e.g., vehicle speed, distance, or behavior).
    Implement a method to trigger accidents by manipulating vehicle parameters or actions.
3. Manipulate vehicle parameters:
    Modify vehicle attributes (e.g., speed, lane change behavior) to create unsafe driving conditions.
    Use traci.vehicle methods to adjust vehicle parameters during the simulation.
4. Integrate accident simulation into the SUMOTrafficSimulator class:
    Add accident triggers and manipulation methods to the SUMOTrafficSimulator class.
    Update the simulation step method to check for accidents and handle collisions.
5. Test the accident simulation:
    Run the simulation with accident triggers and observe the effects of collisions on traffic flow.
    Analyze the simulation results to evaluate the impact of accidents on traffic performance.
    
Implementation Idea 2:

1. Modify initialize_sumo to Include Collision Options
    In the initialize_sumo method, add collision options to the SUMO command to specify how collisions are detected and handled.
2. Add Accident Configuration Parameters
    In the _load_simulation_config method, load accident-related parameters from the simulation configuration.
3. Implement simulate_accident Method
    Create a method to manipulate vehicle parameters and cause collisions.
4. Add Triggers in sumo_step Method
    Modify the sumo_step method to call simulate_accident based on defined triggers.
5. Update Simulation Configuration
    Ensure that the simulation configuration includes accident parameters.
6. Test the Accident Simulation
    Run the simulation with accident triggers and observe the effects of collisions on traffic flow.
    Analyze the simulation results to evaluate the impact of accidents on traffic performance.
"""


class SUMOTrafficSimulator:
    """
    Class responsible for initializing, running, managing, and terminating the SUMO traffic simulation.
    """
    def __init__(self, configs, logger=None):
        self.sumo_configs = configs
        self.logger = logger
        self.metrics = self.sumo_configs['metrics']
        self.simulation_config = self.sumo_configs['simulation']
        self.interface_type = self.simulation_config['interface_type']

    def initialize_sumo(self):
        """
        Initialize the SUMO simulation with proper configurations and error handling.
        """
        self.logger.info("Initializing SUMO simulation.")

        if 'SUMO_HOME' in os.environ:
            tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
            sys.path.append(tools)
        else:
            self.logger.error("SUMO_HOME environment variable not set.")
            sys.exit("Please set the 'SUMO_HOME' environment variable.")

        self._load_simulation_config()
        sumo_binary = sumolib.checkBinary('sumo-gui' if self.gui else 'sumo')
        self.sumo_cmd = [sumo_binary, '-c', self.sumocfg_file]
        if self.no_warning:
            self.sumo_cmd.append('--no-warnings')

        # Add collision options
        self.sumo_cmd += [
            '--collision.action', 'remove',  # Remove vehicles upon collision
            '--collision.check-junctions',   # Check for collisions at junctions
            '--collision.mingap-factor', '0' # Only physical collisions are registered
        ]

        self.connect_to_sumo()
        self.initialize_traffic_signal_controllers()
        self.network_graph = self.build_graph()



    def connect_to_sumo(self):
        """
        Connect to the SUMO simulation using the specified interface (libsumo or traci).
        """
        if self.interface_type == "libsumo":
            libsumo.start(self.sumo_cmd)
            self.sumo_interface = libsumo
        elif self.interface_type == "traci":
            traci.start(self.sumo_cmd)
            self.sumo_interface = traci
        else:
            raise ValueError("Invalid interface type specified.")
        self.simulation_running = True
        self.is_truncated = False
        self.is_terminated = False
        self.simulation_max_steps = int(self.sumo_interface.simulation.getEndTime())
        self.simulation_step = self.sumo_interface.simulation.getTime()

    def close_sumo(self):
        """
        Close the SUMO simulation.
        """
        if self.simulation_running:
            self.logger.info("Closing SUMO simulation.") 
                       
            if self.interface_type == "libsumo":
                libsumo.close()
            elif self.interface_type == "traci":
                traci.close()
            self.simulation_running = False
            self.is_terminated = True

    def _load_simulation_config(self):
        """
        Load initial configuration for the simulation, including traffic lights and detectors.
        """
        self.simulation_seed = self.simulation_config['seed']
        self.gui = self.simulation_config['gui']
        self.no_warning = self.simulation_config['no_warning']
        self.network_name = self.simulation_config['network_name']
        self.interface_type = self.simulation_config['interface_type']
        self.sumocfg_file = os.path.join(
            self.simulation_config['networks_path'],
            self.network_name,
            self.network_name + "_sumo_config.sumocfg"
        )
        random.seed(self.simulation_seed)

        # Load accident configuration
        self.accident_interval = self.simulation_config.get('accident_interval', None)  # e.g., every 100 steps
        self.accident_probability = self.simulation_config.get('accident_probability', 0.0)  # e.g., 0.01 for 1% chance
        self.accident_duration = self.simulation_config.get('accident_duration', 30)  # e.g., 30 seconds

    def simulate_accident(self):
        """
        Simulate an accident by manipulating vehicle parameters to cause a collision.
        """
        # Get all vehicles
        vehicle_ids = self.sumo_interface.vehicle.getIDList()
        if not vehicle_ids:
            self.logger.info("No vehicles in simulation to cause accident")
            return

        # Try to find a pair of vehicles on the same lane
        for lane_id in self.sumo_interface.lane.getIDList():
            vehicles_on_lane = self.sumo_interface.lane.getLastStepVehicleIDs(lane_id)
            if len(vehicles_on_lane) >= 2:
                # Get the first two vehicles (front and back)
                front_vehicle = vehicles_on_lane[0]
                back_vehicle = vehicles_on_lane[1]

                # Set the front vehicle to stop suddenly
                self.sumo_interface.vehicle.setSpeed(front_vehicle, 0)
                self.sumo_interface.vehicle.setDecel(front_vehicle, 9.0)  # Maximum deceleration

                # Disable safety checks for the back vehicle
                self.sumo_interface.vehicle.setSpeedMode(back_vehicle, 0)
                # Increase the speed of the back vehicle
                current_speed = self.sumo_interface.vehicle.getSpeed(back_vehicle)
                self.sumo_interface.vehicle.setSpeed(back_vehicle, current_speed + 10)

                self.logger.info(f"Simulating accident between vehicles {front_vehicle} and {back_vehicle} on lane {lane_id}")

                return

        self.logger.info("No suitable vehicles found on same lane to simulate accident")


    def initialize_traffic_signal_controllers(self):
        """
        Initialize the traffic light controllers for the simulation.
        """

        self.lanes = self.sumo_interface.lane.getIDList()
        self.edges = self.sumo_interface.edge.getIDList()
        self.traffic_light_ids = self.sumo_interface.trafficlight.getIDList()
        self.traffic_signal_controllers = {tls_id: TrafficLightController(tls_id, self.sumo_configs, self.sumo_interface, self.logger) for tls_id in self.traffic_light_ids}
        self.controllers = list(self.traffic_signal_controllers.values())

    def build_graph(self):
        """
        Construct the graph based on the interface type (libsumo or traci).
        """
        if self.interface_type == "libsumo":
            pass  # Not implemented for libsumo
        elif self.interface_type == "traci":
            return self.build_graph_with_traci()
        else:
            raise ValueError("Invalid interface type specified.")

    def build_graph_with_traci(self):
        """
        Construct the traffic network graph using SUMO TraCI methods.
        This graph will be used for Graph Neural Network operations.
        """
        if self.logger:
            self.logger.info("Building the traffic network graph using TraCI.")

        # Initialize node mapping: traffic light IDs to sequential indices
        node_idx_map = {tls_id: idx for idx, tls_id in enumerate(self.traffic_light_ids)}
        num_nodes = len(self.traffic_light_ids)
        # Prepare lists to collect edge indices
        edge_index = [[], []]  # [source_nodes, target_nodes]

        # Set of traffic light nodes for quick lookup
        traffic_light_nodes = set(self.traffic_light_ids)

        # Build the graph by iterating over each traffic light controller
        for tls_id in self.traffic_light_ids:
            src_idx = node_idx_map[tls_id]
            controlled_lanes = self.sumo_interface.trafficlight.getControlledLanes(tls_id)

            for lane_id in controlled_lanes:
                # Get the outgoing connections from the current lane
                links = self.sumo_interface.lane.getLinks(lane_id)
                for link in links:
                    outgoing_lane_id = link[0]
                    # Get the edge ID associated with the outgoing lane
                    edge_id = self.sumo_interface.lane.getEdgeID(outgoing_lane_id)
                    # Get the destination node (junction) of the edge
                    to_node_id = self.sumo_interface.edge.getToJunction(edge_id)
                    # Check if the destination node is controlled by a traffic light
                    if to_node_id in traffic_light_nodes:
                        dest_idx = node_idx_map[to_node_id]
                        # Add an edge from the current node to the destination node
                        edge_index[0].append(src_idx)
                        edge_index[1].append(dest_idx)

        # Convert edge indices to a PyTorch tensor
        edge_index = torch.tensor(edge_index, dtype=torch.long)

        # Store the graph attributes for later use
        self.graph = {
            'num_nodes': num_nodes,
            'edge_index': edge_index,
            'node_idx_map': node_idx_map,
            'idx_node_map': {idx: tls_id for tls_id, idx in node_idx_map.items()}
        }

        if self.logger:
            self.logger.info("Traffic network graph construction completed.")

        return self.graph

    def sumo_step(self, agent_id, action):
        """
        Apply actions and advance the simulation state.
        Check for termination conditions: maximum steps reached or no more vehicles.
        """
        try:
            # Check for maximum steps reached
            if self.simulation_step >= self.simulation_max_steps:
                self.logger.info("Simulation step limit reached. Ending simulation.")
                self.is_truncated = True
                return None, None, True

            # Check if all vehicles have arrived
            if self.sumo_interface.simulation.getMinExpectedNumber() == 0:
                self.logger.info("All vehicles have arrived at their destinations. Ending simulation.")
                self.is_terminated = True
                return None, None, True

            # Trigger accidents based on interval or probability
            if self.accident_interval and self.simulation_step % self.accident_interval == 0:
                self.simulate_accident()
            elif self.accident_probability > 0.0 and random.random() < self.accident_probability:
                self.simulate_accident()

            # Update the traffic light controller with the action
            self.traffic_signal_controllers[agent_id].pseudo_step(action)
            self.sumo_interface.simulationStep()
            self.simulation_step += 1

            # Get observation for the agent
            observation = self.traffic_signal_controllers[agent_id].collect_data()
            reward = -observation[self.metrics['reward_metric']]
            done = self.is_truncated or self.is_terminated

            return observation, reward, done

        except Exception as e:
            self.logger.error(f"Error updating SUMO state: {e}")
            raise

        
    # Function to collect the observation for the agent
    def get_observation_for(self, agent):
        """
        Get the observation for the agent.
        """
        return agent.collect_data()
    
    def get_global_state(self, observations):
        """
        Get the global state representation from the individual agent observations.
        """
        # Aggregate the total queue length from all agents using the queue_length metric
        global_aggregate = sum(obs[(self.metrics ["global_metric"])] for obs in observations.values())
        total_queue_length = {"total_queue_length": global_aggregate}
        return global_aggregate
    
        
    def reset_sumo(self):
        """
        Reset the simulation to initial conditions.
        """
        self.logger.info("Resetting SUMO simulation.")
        self.close_sumo()
        if not self.simulation_running:
            self.connect_to_sumo()


    def run_simulation(self, agent, max_steps=1000):
        """
        Run the simulation for a specified number of steps.
        """
        self.logger.info("Running SUMO simulation.")
        self.initialize_sumo()
        self.simulation_step = 0
        done = False
        while not done and self.simulation_step < max_steps:
            action = agent.get_action()
            observation, reward, done = self.sumo_step(agent.id, action)
            agent.update(observation, reward)
        self.close_sumo()
        self.logger.info("Simulation completed.")
        return agent.total_reward