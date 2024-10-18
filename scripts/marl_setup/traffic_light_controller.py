# traffic_light_controller.py
import numpy as np

class TrafficLightController:
    """
    Represents a controllable traffic light junction with a state machine enforcing regulatory minimum time intervals.
    """
    def __init__(self, tls_id, config, sumo_interface, logger=None):
        self.id = tls_id
        self.config = config
        self.logger = logger
        self.sumo_interface = sumo_interface
        self.configure_traffic_light()

    def configure_traffic_light(self):
        self.phases = self.read_phases()
        # self.current_phase = self.sumo_interface.trafficlight.getPhase(self.id)
        # self.current_phase_start_time = self.sumo_interface.simulation.getTime()
        self.detectors = self.initialize_detectors()
        self.setup_phase_durations()
        self.setup_state_machine()
        self.reset_tl()
        self.build_feature_order()

    def build_feature_order(self):

        self.feature_order = []
        
        if 'current_phase' in self.state_metrics:
            if self.metrics.get('use_phase_one_hot', False):
                num_phases = len(self.phases)
                self.feature_order.extend([f'current_phase_{i}' for i in range(num_phases)])
            else:
                self.feature_order.append('current_phase')
        
        for metric in self.state_metrics:
            if metric != 'current_phase':
                self.feature_order.append(metric)

    def initialize_detectors(self):

        self.metrics = self.config.get('metrics', {})
        self.state_metrics = self.metrics.get('state_metrics', [])
        self.action_type = self.metrics['action_type']
        self.detector_config = self.config.get('detectors', {})

        detectors = []
        controlled_links = self.sumo_interface.trafficlight.getControlledLinks(self.id)
        in_lanes = {link[0] for links in controlled_links for link in links}
        self.detectors_enabled = self.detector_config.get('enabled', [])

        for detector_type in self.detectors_enabled:
            detector_prefix = self.detector_config['detector_prefix'][detector_type]
            detectors.extend(f"{detector_prefix}_{lane}" for lane in in_lanes)
        return detectors

    def collect_data(self):
        """
        Collect data from enabled detectors, return a dictionary of the collected data.
        """
        aggregated_data = {metric: 0.0 for metric in self.state_metrics}
        mean_speed_count = 0
        occupancy_count = 0

        if 'current_phase' in self.state_metrics:
            if self.metrics.get('use_phase_one_hot', False):
                current_phase = self.get_current_phase_one_hot()
                aggregated_data['current_phase'] = current_phase
                # print(f"Current phase one-hot: {current_phase}")
            else:
                aggregated_data['current_phase'] = float(self.current_phase)


        for detector_id in self.detectors:
            if detector_id.startswith('e1det_'):

                if 'vehicle_count' in self.state_metrics:
                    throughput = self.sumo_interface.inductionloop.getLastStepVehicleNumber(detector_id)
                    aggregated_data['throughput'] += throughput
                if 'mean_speed' in self.state_metrics:
                    mean_speed = self.sumo_interface.inductionloop.getLastStepMeanSpeed(detector_id)
                    if mean_speed >= 0:
                        aggregated_data['mean_speed'] += mean_speed
                        mean_speed_count += 1
                if 'occupancy' in self.state_metrics:
                    occupancy = self.sumo_interface.inductionloop.getLastStepOccupancy(detector_id)
                    aggregated_data['occupancy'] += occupancy
                    occupancy_count += 1

            elif detector_id.startswith('e2det_'):
                # Lane Area Detectors (Incoming Lanes)
                if 'queue_length' in self.state_metrics:
                    jam_length = self.sumo_interface.lanearea.getJamLengthVehicle(detector_id)
                    aggregated_data['queue_length'] += jam_length

                if 'queue_length_in_meters' in self.state_metrics:
                    jam_length_meters = self.sumo_interface.lanearea.getJamLengthMeters(detector_id)
                    aggregated_data['queue_length_in_meters'] += jam_length_meters

                if 'halt_count' in self.state_metrics:
                    halt_count = self.sumo_interface.lanearea.getLastStepHaltingNumber(detector_id)
                    aggregated_data['halt_count'] += halt_count

        # Calculate averages if counts are greater than zero
        if mean_speed_count > 0:
            aggregated_data['mean_speed'] /= mean_speed_count
        if occupancy_count > 0:
            aggregated_data['occupancy'] /= occupancy_count

        return aggregated_data


    def get_current_phase_one_hot(self):
        """
        Return the current phase as a one-hot encoded vector.
        """
        # Fetch the current phase from the SUMO interface to ensure it is up-to-date
        self.current_phase = self.sumo_interface.trafficlight.getPhase(self.id)
        
        phase_index = self.current_phase
        num_phases = len(self.phases)
        one_hot = np.zeros(num_phases, dtype=int)  # Initialize with zeros for all phases
        one_hot[phase_index] = 1
        # print(f"Current phase index: {phase_index} for {self.id}")  # Debugging output
        return one_hot

    def read_phases(self):
        """
        Read the TLS programs and fetch the phases for a given traffic light.
        """
        try:
            logic = self.sumo_interface.trafficlight.getAllProgramLogics(self.id)
            phases = logic[0].phases
            self.phase_info = []

            for idx, phase in enumerate(phases):
                phase_type = self.identify_phase_type(phase.state)
                self.phase_info.append({
                    'index': idx,
                    'duration': phase.duration,
                    'state': phase.state,
                    'type': phase_type
                })
            return phases
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error retrieving phases for traffic light {self.id}: {e}")
            return []

    def identify_phase_type(self, state_str):
        """
        Identify the phase type based on the signal state string.
        """
        # Simplified rules for phase identification
        if 'G' in state_str or 'g' in state_str:
            return 'green'
        elif 'y' in state_str or 'Y' in state_str:
            return 'amber'
        elif all(c == 'r' for c in state_str):
            return 'all-red'
        else:
            return 'clearance'

    def setup_phase_durations(self):
        """
        Set up the minimum durations for each phase based on regulatory requirements.
        """
        # Regulatory minimum durations in seconds for each phase type
        self.regulatory_min_durations = {
            'green': 7.0,
            'amber': 3.0,
            'all-red': 1.0,
            'clearance': 3.0
        }

        self.phase_min_durations = {}
        for phase in self.phase_info:
            phase_type = phase['type']
            min_duration = self.regulatory_min_durations.get(phase_type, 0)
            self.phase_min_durations[phase['index']] = min_duration

    def setup_state_machine(self):
        """
        Set up the state machine for traffic light phase transitions.
        """
        num_phases = len(self.phases)
        self.state_machine = {}

        if self.action_type == 'multiphase':
            # In multiphase, the agent can select any phase
            for i in range(num_phases):
                # Allow transitions to any other phase, respecting regulatory requirements
                permissible_phases = list(range(num_phases))
                permissible_phases.remove(i)  # Remove current phase to avoid unnecessary self-transitions
                self.state_machine[i] = permissible_phases

        elif self.action_type == 'binary':
            # In binary, action 0: stay, action 1: change to next phase
            for i in range(num_phases):
                next_phase = (i + 1) % num_phases
                self.state_machine[i] = {
                    0: i,           # Action 0: stay in the current phase
                    1: next_phase   # Action 1: move to the next phase in sequence
                }

    def pseudo_step(self, action):
        """
        Take actions and manage the traffic light phase using state machine transitions.
        """
        try:
            current_time = self.sumo_interface.simulation.getTime()
            elapsed_time = current_time - self.current_phase_start_time

            min_duration = self.phase_min_durations.get(self.current_phase, 0)

            if elapsed_time >= min_duration:
                # Minimum time met, allow phase change or continuation
                if self.action_type == 'multiphase':
                    desired_next_phase = action  # The action specifies the desired next phase
                    permissible_next_phases = self.state_machine.get(self.current_phase, [])

                    if desired_next_phase in permissible_next_phases:
                        # print(f"Changing phase for tl ID {self.id} from {self.current_phase} to {desired_next_phase}")
                        self.sumo_interface.trafficlight.setPhase(self.id, desired_next_phase)
                        # Update phase and timers
                        self.phase_changes.append({
                            'time': current_time,
                            'old_phase': self.current_phase,
                            'new_phase': desired_next_phase
                        })
                        self.current_phase = desired_next_phase
                        # print(f"Current phase updated to: {self.current_phase} for {self.id}") # Debug: It is updating the phase as expected
                        self.current_phase_start_time = current_time

                elif self.action_type == 'binary':
                    # Get the permissible next phase based on action
                    action = int(action)  # Ensure action is an integer 0 or 1
                    permissible_actions = self.state_machine.get(self.current_phase, {})
                    
                    if action == 1:
                        # Change to the next phase
                        next_phase = permissible_actions[action]
                        self.sumo_interface.trafficlight.setPhase(self.id, next_phase)
                        
                        # Update phase and timers if phase has changed
                        self.phase_changes.append({
                            'time': current_time,
                            'old_phase': self.current_phase,
                            'new_phase': next_phase
                        })
                        self.current_phase = next_phase
                        self.current_phase_start_time = current_time

                    else:

                        # Increment the current phase duration
                        increment = 5.0  # Extend the phase by 5 seconds
                        self.sumo_interface.trafficlight.setPhaseDuration(self.id, increment)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error executing action for traffic light {self.id}: {e}")
            raise


    def reset_tl(self):
        """
        Reset the traffic light to its initial state with a random phase.
        """

        try:
            # Assign a random initial phase
            initial_phase = np.random.choice(len(self.phases))
            self.sumo_interface.trafficlight.setPhase(self.id, initial_phase)
            self.current_phase = initial_phase
            self.current_phase_start_time = self.sumo_interface.simulation.getTime()
            # Introduce a random offset to the phase start time
            # random_offset = np.random.uniform(0, self.phase_min_durations.get(self.current_phase, 5))
            # self.current_phase_start_time = self.sumo_interface.simulation.getTime() - random_offset
            self.phase_changes = []

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error resetting traffic light {self.id}: {e}")
            raise
