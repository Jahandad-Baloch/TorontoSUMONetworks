import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv

class DQNAgent(nn.Module):
    """ 
    Deep Q-Network for individual agents.
    """
    def __init__(self, input_dim, hidden_dim, action_dim):
        super(DQNAgent, self).__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_dim, action_dim)
        
    def forward(self, x):
        x = self.relu(self.fc1(x))
        q_values = self.fc2(x)
        return q_values


class GNNAgent(nn.Module):
    """ 
    Graph Neural Network for individual agents.
    """
    def __init__(self, input_dim, hidden_dim, action_dim, edge_index):
        super(GNNAgent, self).__init__()
        self.conv1 = GCNConv(input_dim, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, hidden_dim)
        self.fc = nn.Linear(hidden_dim, action_dim)
        self.edge_index = edge_index  # Edge indices for the graph
    
    def forward(self, x):
        x = F.relu(self.conv1(x, self.edge_index))
        x = F.relu(self.conv2(x, self.edge_index))
        q_values = self.fc(x)
        return q_values


class LSTMAgent(nn.Module):
    """ 
    LSTM-based network for individual agents.
    """
    def __init__(self, input_dim, hidden_dim, action_dim):
        super(LSTMAgent, self).__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, action_dim)
        
    def forward(self, x):
        x, _ = self.lstm(x)
        q_values = self.fc(x[:, -1, :])
        return q_values
    

class GRUAgent(nn.Module):
    """ 
    GRU-based network for individual agents.
    """
    def __init__(self, input_dim, hidden_dim, action_dim):
        super(GRUAgent, self).__init__()
        self.gru = nn.GRU(input_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, action_dim)
        
    def forward(self, x):
        x, _ = self.gru(x)
        q_values = self.fc(x[:, -1, :])
        return q_values
    

class AttentionAgent(nn.Module):
    """ 
    Attention-based network for individual agents.
    """
    def __init__(self, input_dim, hidden_dim, action_dim):
        super(AttentionAgent, self).__init__()
        self.fc = nn.Linear(input_dim, hidden_dim)
        self.attn = nn.Linear(hidden_dim, 1)
        self.fc2 = nn.Linear(input_dim, action_dim)
        
    def forward(self, x):
        x = F.relu(self.fc(x))
        attn_weights = F.softmax(self.attn(x), dim=1)
        x = torch.sum(attn_weights * x, dim=1)
        q_values = self.fc2(x)
        return q_values
    
# agents/networks.py

class CNNAgent(nn.Module):
    """Convolutional Neural Network Agent."""
    def __init__(self, input_channels, action_dim):
        super(CNNAgent, self).__init__()
        self.conv1 = nn.Conv2d(input_channels, 32, kernel_size=3, stride=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=1)
        self.fc1 = nn.Linear(64 * 6 * 6, 128)  # Adjust dimensions based on input size
        self.fc2 = nn.Linear(128, action_dim)
    
    def forward(self, x):
        # x should have shape [batch_size, input_channels, height, width]
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = x.view(x.size(0), -1)  # Flatten
        x = F.relu(self.fc1(x))
        q_values = self.fc2(x)
        return q_values

    
class RNNAgent(nn.Module):
    """ 
    RNN-based network for individual agents.
    """
    def __init__(self, input_dim, hidden_dim, action_dim):
        super(RNNAgent, self).__init__()
        self.rnn = nn.RNN(input_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, action_dim)
        
    def forward(self, x):
        x, _ = self.rnn(x)
        q_values = self.fc(x[:, -1, :])
        return q_values
    
class BiRNNAgent(nn.Module):
    """ 
    Bidirectional RNN-based network for individual agents.
    """
    def __init__(self, input_dim, hidden_dim, action_dim):
        super(BiRNNAgent, self).__init__()
        self.rnn = nn.RNN(input_dim, hidden_dim, batch_first=True, bidirectional=True)
        self.fc = nn.Linear(2 * hidden_dim, action_dim)
        
    def forward(self, x):
        x, _ = self.rnn(x)
        q_values = self.fc(x[:, -1, :])
        return q_values
    


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

