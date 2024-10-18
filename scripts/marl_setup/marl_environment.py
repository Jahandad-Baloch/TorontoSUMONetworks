import gymnasium as gym
from gymnasium import spaces
import numpy as np
import torch
from sumo_traffic_simulator import SUMOTrafficSimulator


class TrafficSignalControlEnv(gym.Env):
    """
    Optimized Gymnasium environment for multi-agent traffic signal control using SUMO.
    """
    def __init__(self, configs, logger=None):
        super().__init__()
        self.config = configs
        self.logger = logger
        self.simulator = SUMOTrafficSimulator(self.config, self.logger)
        self.simulator.initialize_sumo()
        self.initialize_environment()

    def initialize_environment(self):
        self.metrics = self.simulator.metrics
        self.action_type = self.metrics['action_type']
        self.agents = self.simulator.controllers
        self.action_spaces = {agent.id: self.get_action_space(agent) for agent in self.agents}
        self.observation_spaces = {agent.id: self.get_observation_space(agent) for agent in self.agents}
        self.edge_index = self.simulator.network_graph['edge_index']
        self.state_metrics = self.metrics['state_metrics']
        self.global_metric_name = self.metrics['global_metric']
        self.reward_metric_name = self.metrics['reward_metric']
        self.reward_function = self.metrics['reward_function']

    def reset(self):
        """ 
        Reset the environment for a new episode.
        """
        self.logger.info("Resetting environment for a new episode.")
        self.simulator.close_sumo()
        self.simulator.connect_to_sumo()

        observations = {}
        global_state_values = []
        
        for agent in self.agents:
            features = agent.collect_data()
            
            # Create tensors for each feature and store them in the agent's observations
            agent_obs = {}
            for k, v in features.items():
                agent_obs[k] = torch.tensor(v, dtype=torch.float32)
            
            # Extract global metric and reward metric values
            global_state_values.append(agent_obs[self.global_metric_name])
            
            # Concatenate all feature values to create the final tensor for this agent
            concatenated_features = torch.cat([v.flatten() if isinstance(v, torch.Tensor) else torch.tensor([v], dtype=torch.float32) for v in agent_obs.values()])
            
            # Store the concatenated tensor
            observations[agent.id] = concatenated_features

        # Compute global state using the selected global metric
        global_state = torch.stack(global_state_values).sum()
        

        
        return observations, global_state

    def step(self, actions):
        """
        Take a step in the environment.
        """
        done = all(self.simulator.sumo_step(agent_id, action) for agent_id, action in actions.items())
        if done:
            return None, None, None, done, {}

        observations = {}
        global_state_values = []
        reward_values = []

        for agent in self.agents:
            features = agent.collect_data()
            
            # Create tensors for each feature and store them in the agent's observations
            agent_obs = {}
            for k, v in features.items():
                agent_obs[k] = torch.tensor(v, dtype=torch.float32)

            # Extract global metric and reward metric values
            global_state_values.append(agent_obs[self.global_metric_name])
            # reward_values.append(agent_obs[self.reward_metric_name])
            
            # Concatenate all feature values to create the final tensor for this agent
            concatenated_features = torch.cat([v.flatten() if isinstance(v, torch.Tensor) else torch.tensor([v], dtype=torch.float32) for v in agent_obs.values()])
            
            # Store the concatenated tensor
            observations[agent.id] = concatenated_features

        # Compute global state and reward
        global_state = torch.stack(global_state_values).sum()
        # aggregated_reward = torch.stack(reward_values).sum()
        aggregated_reward = self.compute_reward(observations)

        return observations, global_state, aggregated_reward, False, {}

    def compute_reward(self, observations):
        if self.reward_function == 'global':
            # Use global metrics
            reward = self.compute_global_reward(observations)
        elif self.reward_function == 'difference':
            # Compute difference rewards
            reward = self.compute_difference_reward(observations)
        elif self.reward_function == 'shaped':
            # Use shaped rewards
            reward = self.compute_shaped_reward(observations)
        else:
            raise ValueError(f"Unknown reward function: {self.reward_function}")
        return reward

    
    def compute_global_reward(self, observations):
        global_state_values = []
        for agent in self.agents:
            global_state_values.append(observations[agent.id][self.global_metric_name])
        global_state = torch.stack(global_state_values).sum()
        return global_state
    
    def compute_difference_reward(self, observations):
        pass
    def compute_shaped_reward(self, observations):
        pass
    def close(self):
        self.logger.info("Environment closing.")
        self.simulator.close_sumo()

    def update_graph(self):
        """ Load or update the graph only when necessary. """
        self.graph = self.simulator.build_graph()
        edge_index = self.graph['edge_index']
        return edge_index

    def get_action_space(self, agent):
        if self.action_type == 'binary':
            return spaces.Discrete(2)
        elif self.action_type == 'multiphase':
            return spaces.Discrete(len(agent.phases))

    def get_observation_space(self, agent):

        num_state_metrics = len(self.metrics["state_metrics"])
        num_phases = len(agent.phases)
        if self.config['metrics']['use_phase_one_hot']:
            obs_dim = num_state_metrics + num_phases - 1
        else:
            obs_dim = num_state_metrics

        return spaces.Box(low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32)

