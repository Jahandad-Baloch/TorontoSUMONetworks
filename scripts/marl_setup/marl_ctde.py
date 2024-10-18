import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import Adam

# from TSCMARL.utils import ReplayBuffer, ConfigLoader, LoggerSetup
# from TSCMARL.marl_environment import TrafficSignalControlEnv
from utils import ReplayBuffer, ConfigLoader, LoggerSetup, ModelParams
from marl_environment import TrafficSignalControlEnv
from agent_networks import DQNAgent, GNNAgent, MixingNetwork


class TSCMARL(nn.Module):
    def __init__(self, config_path, logger=None):
        super(TSCMARL, self).__init__()
        self.config = ConfigLoader.load_config(config_path)
        self.logger = LoggerSetup.setup_logger(
            self.__class__.__name__.lower(),
            self.config['logging']['log_dir'],
            self.config['logging']['log_level']
        )
        self.model_params = ModelParams(self.config)
        self.device = self.model_params.device
        self.batch_size = self.model_params.batch_size
        self.env = TrafficSignalControlEnv(self.config, logger=self.logger)
        self.agents = self.env.agents
        self.action_type = self.env.action_type
        self.edge_index = self.env.edge_index
        self.num_agents = len(self.env.agents)
        self.replay_buffer = ReplayBuffer(self.model_params.buffer_size, self.batch_size)
        self.initialize_models() 
        self.optimizer = Adam(
            list(self.agent_nets.parameters()) + list(self.mixing_net.parameters()), 
            lr=self.model_params.learning_rate
        )
        
    def initialize_models(self):
        hidden_dim = self.model_params.hidden_dim
        hypernet_embed_dim = self.model_params.hypernet_embed_dim

        # print("Observation spaces", self.env.observation_spaces)
        # print("Action spaces", self.env.action_spaces)

        self.agent_nets = nn.ModuleDict()
        for agent in self.agents:
            obs_dim = self.env.observation_spaces[agent.id].shape[0]
            action_dim = self.env.action_spaces[agent.id].n
            self.agent_nets[agent.id] = DQNAgent(obs_dim, hidden_dim, action_dim).to(self.device)

        # Initialize mixing network
        self.mixing_net = MixingNetwork(
            num_agents=self.num_agents,
            state_dim=1,
            hypernet_embed_dim=hypernet_embed_dim
        ).to(self.device)

        # Initialize target network        
        self.target_net = MixingNetwork(
            num_agents=self.num_agents,
            state_dim=1,
            hypernet_embed_dim=hypernet_embed_dim
        ).to(self.device)
        
        if self.logger:
            self.logger.info(f"Initialized TSCMARL model with {self.num_agents} agents")

    def aggregate_q_values(self, obs_batch, state_batch):
        # batch_size = state_batch.size(0)

        max_q_values_by_agent = []
        for agent in self.agents:
            obs = obs_batch[agent.id].to(self.device)  # Shape: [batch_size, obs_dim]
            agent_net = self.agent_nets[agent.id]
            q_values = agent_net(obs)  # Shape: [batch_size, action_dim]
            # Select the maximum Q-value per agent
            max_q_values, _ = q_values.max(dim=1)  # Shape: [batch_size]
            max_q_values_by_agent.append(max_q_values)
        
        max_q_values_by_agent = torch.stack(max_q_values_by_agent, dim=1)  # Shape: [batch_size, num_agents]
        combined_q_values = self.mixing_net(max_q_values_by_agent, state_batch.to(self.device))

        return combined_q_values

    def select_actions(self, observations):
        actions = {}
        for agent in self.agents:
            agent_net = self.agent_nets[agent.id]
            obs = observations[agent.id].to(self.device)
            with torch.no_grad():
                q_values = agent_net(obs)
                action = q_values.argmax().item()
                actions[agent.id] = action
        return actions

    def train_step(self):

        if len(self.replay_buffer) < self.batch_size:
            return 0

        batch = self.replay_buffer.sample(self.batch_size)
        
        # Unpack the batch
        (
            observations_batch,
            global_states_batch,
            actions_batch,
            rewards_batch,
            next_observations_batch,
            next_global_states_batch,
            dones_batch
        ) = batch
        
        # Process observations per agent
        obs_batch = {agent.id: [] for agent in self.agents}
        next_obs_batch = {agent.id: [] for agent in self.agents}
        actions_batch_per_agent = {agent.id: [] for agent in self.agents}
        rewards_batch_per_agent = {agent.id: [] for agent in self.agents}
        
        state_batch = []
        next_state_batch = []
        
        for (
            obs_dict,
            global_state,
            next_obs_dict,
            next_global_state,
            action_dict,
            reward_dict
        ) in zip(
            observations_batch,
            global_states_batch,
            next_observations_batch,
            next_global_states_batch,
            actions_batch,
            rewards_batch
        ):
            for agent_id in obs_dict.keys():
                obs_batch[agent_id].append(obs_dict[agent_id])
                next_obs_batch[agent_id].append(next_obs_dict[agent_id])
                actions_batch_per_agent[agent_id].append(action_dict[agent_id])
                rewards_batch_per_agent[agent_id].append(reward_dict[agent_id])
            
            # Ensure state_values are tensors of shape [1]
            state_values = global_state.to(self.device).view(-1)  # Shape: [1]
            next_state_values = next_global_state.to(self.device).view(-1)  # Shape: [1]
            
            # Append to state batches
            state_batch.append(state_values)
            next_state_batch.append(next_state_values)
        
        # Convert lists to tensors
        for agent_id in obs_batch.keys():
            obs_batch[agent_id] = torch.stack(obs_batch[agent_id]).to(self.device)  # Shape: [batch_size, obs_dim]
            next_obs_batch[agent_id] = torch.stack(next_obs_batch[agent_id]).to(self.device)
            actions_batch_per_agent[agent_id] = torch.tensor(
                actions_batch_per_agent[agent_id], dtype=torch.long
            ).to(self.device)
            rewards_batch_per_agent[agent_id] = torch.tensor(
                rewards_batch_per_agent[agent_id], dtype=torch.float32
            ).to(self.device)
        
        # Stack state batches
        state_batch = torch.stack(state_batch).to(self.device)  # Shape: [batch_size, state_dim]
        next_state_batch = torch.stack(next_state_batch).to(self.device)
        dones_batch = torch.tensor(dones_batch, dtype=torch.float32).to(self.device)
        
        # Verify shapes
        # print(f"state_batch shape: {state_batch.shape}")
        # print(f"next_state_batch shape: {next_state_batch.shape}")
        
        # Sum rewards across agents if needed
        rewards_batch_per_agent_total = torch.stack(
            [rewards_batch_per_agent[agent.id] for agent in self.agents], dim=1
        ).sum(dim=1)
        
        # Proceed with forward pass and loss computation
        q_total = self.aggregate_q_values(obs_batch, state_batch)
        
        # Compute target Q-values
        with torch.no_grad():
            next_q_total = self.aggregate_q_values(next_obs_batch, next_state_batch)
            target_q_total = rewards_batch_per_agent_total + self.config['training']['gamma'] * (1 - dones_batch) * next_q_total
        
        # Compute loss
        loss = F.mse_loss(q_total, target_q_total)
        
        # Optimize the networks
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.parameters(), self.config['training']['grad_norm_clip'])
        self.optimizer.step()
        
        return loss.item()

    def train(self, episodes):
        for episode in range(episodes):
            observations, global_state = self.env.reset()
            episode_reward = 0
            done = False
            total_loss = 0
            step = 0
            
            while not done:
                actions = self.select_actions(observations)
                next_observations, next_global_state, rewards, done, _ = self.env.step(actions)
                self.replay_buffer.push(observations, global_state, actions, rewards, next_observations, next_global_state, done)
                print("Step: ", step)
                print(observations, global_state, actions, rewards, next_observations, next_global_state, done)
                if step >= self.model_params.warmup_steps:
                    loss = self.train_step()
                    total_loss += loss
                    if step % 50 == 0:
                        self.logger.info(f"Step: {step}, Loss: {loss}")

                observations = next_observations
                global_state = next_global_state
                episode_reward += sum(rewards.values())
                
                if done:
                    break

                step += 1
                
                if step % self.model_params.update_target_rate == 0:
                    self.update_target_network()

            self.logger.info(f"Episode: {episode}, Episode loss: {total_loss}, Total Reward: {episode_reward}")

        self.env.close()

    def update_target_network(self):
        self.target_net.load_state_dict(self.mixing_net.state_dict())
        self.logger.info("Updated target network")
        
    def save_model(self, path):
        torch.save(self.agent_net.state_dict(), path)
        self.logger.info(f"Saved model at {path}")
        
    def load_model(self, path):
        self.agent_net.load_state_dict(torch.load(path))
        self.logger.info(f"Loaded model from {path}")


if __name__ == '__main__':
    config_path = 'TSCMARL/configurations/main_config.yaml'

    model = TSCMARL(config_path)
    model.train(100)