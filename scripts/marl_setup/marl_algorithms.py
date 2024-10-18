import torch
import torch.nn as nn
import torch.nn.functional as F

""" 
MARL algorithms for traffic signal control.
Classes: MixingNetwork, MADDPG, MATD3, MATD3GNN
"""
# algorithms/marl_algorithm.py

class MARLAlgorithm:
    def __init__(self, agents, env, config):
        self.agents = agents
        self.env = env
        self.config = config
    
    def select_actions(self, observations):
        raise NotImplementedError
    
    def train_step(self, batch):
        raise NotImplementedError
    
    def update_target_networks(self):
        raise NotImplementedError

class ActorNetwork(nn.Module):
    def __init__(self, observation_space, action_space):
        super(ActorNetwork, self).__init__()
        self.observation_space = observation_space
        self.action_space = action_space
        self.fc1 = nn.Linear(observation_space.shape[0], 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, action_space.shape[0])
    
    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = torch.tanh(self.fc3(x))
        return x
    
class CriticNetwork(nn.Module):
    def __init__(self, observation_space, action_space):
        super(CriticNetwork, self).__init__()
        self.observation_space = observation_space
        self.action_space = action_space
        self.fc1 = nn.Linear(observation_space.shape[0] + action_space.shape[0], 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, 1)
    
    def forward(self, x, u):
        x = F.relu(self.fc1(torch.cat([x, u], dim=1)))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x


class MADDPG(MARLAlgorithm):
    """ 
    Multi-Agent Deep Deterministic Policy Gradient (MADDPG) algorithm.
    """
    def __init__(self, agents, env, config):
        super(MADDPG, self).__init__(agents, env, config)
        self.agent_ids = list(self.agents.keys())
        self.agent_action_spaces = {agent_id: self.env.action_spaces[agent_id] for agent_id in self.agent_ids}
        self.agent_observation_spaces = {agent_id: self.env.observation_spaces[agent_id] for agent_id in self.agent_ids}
        
        # Initialize hyperparameters
        self.gamma = self.config['gamma']
        self.tau = self.config['tau']
        self.batch_size = self.config['batch_size']
        self.lr_actor = self.config['lr_actor']
        self.lr_critic = self.config['lr_critic']
        
        # Initialize actor and critic networks for each agent
        self.actor_networks = {agent_id: ActorNetwork(self.agent_observation_spaces[agent_id], self.agent_action_spaces[agent_id]) for agent_id in self.agent_ids}
        self.critic_networks = {agent_id: CriticNetwork(self.agent_observation_spaces[agent_id], self.agent_action_spaces[agent_id]) for agent_id in self.agent_ids}
        
        # Initialize target networks
        self.target_actor_networks = {agent_id: ActorNetwork(self.agent_observation_spaces[agent_id], self.agent_action_spaces[agent_id]) for agent_id in self.agent_ids}
        self.target_critic_networks = {agent_id: CriticNetwork(self.agent_observation_spaces[agent_id], self.agent_action_spaces[agent_id]) for agent_id in self.agent_ids}
        
        # Copy weights from actor and critic networks to target networks
        for agent_id in self.agent_ids:
            self.target_actor_networks[agent_id].load_state_dict(self.actor_networks[agent_id].state_dict())
            self.target_critic_networks[agent_id].load_state_dict(self.critic_networks[agent_id].state_dict())
        
        # Initialize optimizers for actor and critic networks
        self.actor_optimizers = {agent_id: torch.optim.Adam(self.actor_networks[agent_id].parameters(), lr=self.lr_actor) for agent_id in self.agent_ids}
        self.critic_optimizers = {agent_id: torch.optim.Adam(self.critic_networks[agent_id].parameters(), lr = self.lr_critic) for agent_id in self.agent_ids}
        
    def select_actions(self, observations):
        actions = {}
        for agent_id, agent_obs in observations.items():
            actions[agent_id] = self.actor_networks[agent_id](agent_obs)
        return actions
    
    def train_step(self, batch):
        # Extract batch data
        observations = batch['observations']
        actions = batch['actions']
        rewards = batch['rewards']
        next_observations = batch['next_observations']
        dones = batch['dones']
        
        # Update critic networks
        for agent_id in self.agent_ids:
            next_actions = {aid: self.target_actor_networks[aid](next_obs) for aid, next_obs in next_observations.items()}
            target_q_values = self.target_critic_networks[agent_id](next_observations[agent_id], next_actions)
            target_q_values = rewards[agent_id] + self.gamma * target_q_values * (1 - dones[agent_id])
            
            q_values = self.critic_networks[agent_id](observations[agent_id], actions[agent_id])
            critic_loss = F.mse_loss(q_values, target_q_values)
            
            self.critic_optimizers[agent_id].zero_grad()
            critic_loss.backward()
            self.critic_optimizers[agent_id].step()
        
        # Update actor networks
        for agent_id in self.agent_ids:
            actor_loss = -self.critic_networks[agent_id](observations[agent_id], actions[agent_id]).mean()
            
            self.actor_optimizers[agent_id].zero_grad()
            actor_loss.backward()
            self.actor_optimizers[agent_id].step()
        
        return actor_loss.item(), critic_loss.item()
    
    def update_target_networks(self):
        for agent_id in self.agent_ids:
            for target_param, param in zip(self.target_actor_networks[agent_id].parameters(), self.actor_networks[agent_id].parameters()):
                target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)
            
            for target_param, param in zip(self.target_critic_networks[agent_id].parameters(), self.critic_networks[agent_id].parameters()):
                target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)
                
                

class MixingNetwork(nn.Module):
    """ 
    Hypernetwork for mixing agent Q-values
    """
    def __init__(self, num_agents, state_dim, hypernet_embed_dim):
        super(MixingNetwork, self).__init__()
        self.num_agents = num_agents
        self.state_dim = state_dim
        self.hypernet_embed_dim = hypernet_embed_dim
        
        # Hypernetworks for mixing weights and biases
        self.hyper_w1 = nn.Sequential(
            nn.Linear(state_dim, hypernet_embed_dim),
            nn.ReLU(),
            nn.Linear(hypernet_embed_dim, num_agents * hypernet_embed_dim)
        )
        self.hyper_w2 = nn.Sequential(
            nn.Linear(state_dim, hypernet_embed_dim),
            nn.ReLU(),
            nn.Linear(hypernet_embed_dim, hypernet_embed_dim)
        )
        
        self.hyper_b1 = nn.Linear(state_dim, hypernet_embed_dim)
        self.hyper_b2 = nn.Sequential(
            nn.Linear(state_dim, hypernet_embed_dim),
            nn.ReLU(),
            nn.Linear(hypernet_embed_dim, 1)
        )
        
    def forward(self, agent_qs, state):
        batch_size = agent_qs.size(0)
        
        # Generate hypernet weights for the first layer
        w1 = torch.abs(self.hyper_w1(state))  # Shape: [batch_size, num_agents * embed_dim]
        w1 = w1.view(batch_size, self.num_agents, self.hypernet_embed_dim)  # Shape: [batch_size, num_agents, embed_dim]
        
        b1 = self.hyper_b1(state).view(batch_size, 1, self.hypernet_embed_dim)  # Shape: [batch_size, 1, embed_dim]
        
        # Reshape agent_qs for batch multiplication
        agent_qs = agent_qs.view(batch_size, 1, self.num_agents)  # Shape: [batch_size, 1, num_agents]
        
        # First layer transformation
        hidden = F.elu(torch.bmm(agent_qs, w1) + b1)  # Shape: [batch_size, 1, embed_dim]
        
        # Generate hypernet weights for the second layer
        w2 = torch.abs(self.hyper_w2(state)).view(batch_size, self.hypernet_embed_dim, 1)  # Shape: [batch_size, embed_dim, 1]
        b2 = self.hyper_b2(state).view(batch_size, 1, 1)  # Shape: [batch_size, 1, 1]
        
        # Second layer transformation
        y = torch.bmm(hidden, w2) + b2  # Shape: [batch_size, 1, 1]
        q_total = y.view(batch_size)  # Shape: [batch_size]
        return q_total

