import math
import random
from collections import deque
import torch
import torch.optim as optim
import torch.nn.functional as F

from procedures.matching.model import (
    MatchingModel,
)  # ensure this model outputs num_actions Q-values


# Dummy environment for demonstration purposes
class DummyEnv:
    def __init__(self):
        self.reset()

    def reset(self):
        # Example state: tuple of (hobbies_ids, age_tensor)
        # hobbies_ids: tensor of shape [1, seq_len] (e.g., 5 hobbies)
        hobbies_ids = torch.randint(0, 1000, (1, 5))
        # age_tensor: tensor of shape [1, 1] (e.g., a normalized age)
        age_tensor = torch.tensor([[random.uniform(18, 80)]])
        return hobbies_ids, age_tensor

    def step(self):
        # Dummy step: new random state, random reward, and a small chance to end the episode
        next_state = self.reset()
        reward = random.random()  # dummy reward for demonstration
        done = random.random() < 0.1  # 10% chance to end episode
        return next_state, reward, done, {}


# Replay memory to store transitions
class ReplayMemory:
    def __init__(self, capacity):
        self.memory = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)


# Hyperparameters
num_episodes = 200
batch_size = 32
gamma = 0.99
learning_rate = 1e-3
target_update = 10
epsilon_start = 1.0
epsilon_end = 0.1
epsilon_decay = 200  # controls rate of decay
num_actions = 2  # e.g., 0: no match, 1: match
vocab_size = 1000
embed_dim = 32

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Instantiate our Q-network (policy network) and a target network
policy_net = MatchingModel(vocab_size, embed_dim).to(device)
target_net = MatchingModel(vocab_size, embed_dim).to(device)
target_net.load_state_dict(policy_net.state_dict())
target_net.eval()

optimizer = optim.Adam(policy_net.parameters(), lr=learning_rate)
memory = ReplayMemory(10000)
steps_done = 0


def select_action(state):
    """Epsilon-greedy action selection."""
    global steps_done
    epsilon = epsilon_end + (epsilon_start - epsilon_end) * math.exp(
        -1.0 * steps_done / epsilon_decay
    )
    steps_done += 1
    if random.random() < epsilon:
        # Random action
        return torch.tensor(
            [[random.randrange(num_actions)]], device=device, dtype=torch.long
        )
    else:
        # State is a tuple: (hobbies_ids, age_tensor)
        hobbies_ids, age_tensor = state
        hobbies_ids = hobbies_ids.to(device)
        age_tensor = age_tensor.to(device)
        with torch.no_grad():
            q_values = policy_net(
                hobbies_ids, age_tensor
            )  # expect shape [batch, num_actions]
            return q_values.argmax(dim=1).view(1, 1)


def optimize_model():
    if len(memory) < batch_size:
        return
    transitions = memory.sample(batch_size)
    # Unpack the batch of transitions
    batch_state, batch_action, batch_reward, batch_next_state, batch_done = zip(
        *transitions
    )

    # Process states: each state is a tuple (hobbies_ids, age_tensor)
    batch_hobbies_ids = torch.cat([s[0] for s in batch_state]).to(
        device
    )  # shape: [batch, seq_len]
    batch_age = torch.cat([s[1] for s in batch_state]).to(device)  # shape: [batch, 1]
    batch_action = torch.cat(batch_action).to(device)  # shape: [batch, 1]
    batch_reward = torch.tensor(
        batch_reward, dtype=torch.float32, device=device
    ).unsqueeze(1)
    batch_done = torch.tensor(batch_done, dtype=torch.float32, device=device).unsqueeze(
        1
    )

    # Process next states
    batch_next_hobbies_ids = torch.cat([s[0] for s in batch_next_state]).to(device)
    batch_next_age = torch.cat([s[1] for s in batch_next_state]).to(device)

    # Compute current Q-values: Q(s, a) using policy_net
    state_action_values = policy_net(batch_hobbies_ids, batch_age).gather(
        1, batch_action
    )

    # Compute next Q-values using target network and calculate expected Q-values
    next_q_values = (
        target_net(batch_next_hobbies_ids, batch_next_age)
        .max(1)[0]
        .detach()
        .unsqueeze(1)
    )
    expected_state_action_values = batch_reward + gamma * next_q_values * (
        1 - batch_done
    )

    # Compute loss (Mean Squared Error)
    loss = F.mse_loss(state_action_values, expected_state_action_values)

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()


# Main training loop
env = DummyEnv()
for episode in range(num_episodes):
    state = env.reset()
    total_reward = 0.0
    done = False
    while not done:
        action = select_action(state)
        next_state, reward, done, _ = env.step()
        total_reward += reward
        memory.push(state, action, reward, next_state, done)
        state = next_state
        optimize_model()

    if episode % target_update == 0:
        target_net.load_state_dict(policy_net.state_dict())

    print(f"Episode {episode}: Total Reward: {total_reward:.2f}")
