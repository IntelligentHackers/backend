import torch
import torch.nn as nn


class MatchingModel(nn.Module):
    def __init__(self, embed_dim: int):
        super(MatchingModel, self).__init__()
        self.model = nn.Sequential(
            nn.Linear(embed_dim, 1024),
            nn.GELU(),
            nn.Linear(1024, 256),
            nn.GELU(),
            nn.Linear(256, embed_dim)
        )

    def forward(self, vector: torch.tensor):
        return self.model(vector)
