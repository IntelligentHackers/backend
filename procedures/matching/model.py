import torch
import torch.nn as nn
import torch.nn.functional as F
import math
import random
from collections import deque


class MatchingModel(nn.Module):
    def __init__(self, vocab_size: int, embed_dim: int):
        super(MatchingModel, self).__init__()
        self.user_embedding = nn.Embedding(vocab_size, embed_dim)
        self.age_mlp = nn.Sequential(
            nn.Linear(1, 16), nn.GELU(), nn.Linear(16, embed_dim)
        )
        self.final_mlp = nn.Sequential(
            nn.Linear(embed_dim * 2, 64), nn.GELU(), nn.Linear(64, 1)
        )

    def forward(self, hobbies_ids, age_tensor):
        """Forward pass of the MatchingModel.
        Args:
            hobbies_ids (torch.Tensor): Tensor of indices for user hobbies with shape [batch_size, seq_len].
            age_tensor (torch.Tensor): Tensor of ages with shape [batch_size, 1].
        Returns:
            torch.Tensor: Matching score for the given inputs.
        """
        # Get hobby embeddings and average over sequence length
        hobby_embed = self.user_embedding(hobbies_ids).mean(dim=1)

        # Process age input
        age_embed = self.age_mlp(age_tensor)

        # Concatenate the embeddings
        combined = torch.cat([hobby_embed, age_embed], dim=1)

        # Get the matching score
        score = self.final_mlp(combined)
        return score
