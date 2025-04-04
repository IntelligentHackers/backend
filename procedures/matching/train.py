import math
import random
import torch
import torch.nn as nn
import torch.optim as optim
from procedures.matching.model import MatchingModel
from procedures.matching.parameters import (
    embed_dim,
    learning_rate,
    batch_size,
    gamma,
)

device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")

# Instantiate our Q-network (policy network) and a target network
policy_net = MatchingModel(embed_dim).to(device)
target_net = MatchingModel(embed_dim).to(device)
target_net.load_state_dict(policy_net.state_dict())
target_net.eval()

optimizer = optim.Adam(policy_net.parameters(), lr=learning_rate)
steps_done = 0


import torch
import torch.nn.functional as F
import random

def train_dqn(model: nn.Module, transitions):
    if len(transitions) < batch_size:
        return

    batch = random.sample(transitions, batch_size)
    rewards, inputs, outputs = zip(*batch)

    inputs = torch.stack([torch.tensor(i, dtype=torch.float32) for i in inputs]).squeeze(-1).to(device=device)  # shape: [B, embed_dim]
    outputs = torch.stack([torch.tensor(o, dtype=torch.float32) for o in outputs]).squeeze(-1).to(device=device)  # shape: [B, embed_dim]
    rewards = torch.tensor(rewards, dtype=torch.float32).to(device=device)  # shape: [B]

    # Forward pass
    q_inputs = model(inputs)  # [B, embed_dim]

    # Dot-product as Q-value estimate: Q(s, a) = q(s) ⋅ a
    q_values = torch.sum(q_inputs * outputs, dim=1)  # shape: [B]

    # Targets: we only have immediate rewards (no next state)
    targets = rewards

    # Loss
    loss = F.mse_loss(q_values, targets)

    # Backprop
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    return loss.item()
