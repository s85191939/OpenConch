"""
Fusion Gate — combines the three STRATUM strata.

A learned per-token gate that weights the contributions from:
- Stratum 1 (Episodic Memory): distant factual recall
- Stratum 2 (Mamba hidden states): local/syntactic reasoning
- Stratum 3 (Anchor Attention): precision cross-comparisons

The gate learns different weightings per token per layer. In practice:
- Most tokens lean heavily on S2 (Mamba) — it's the default
- Tokens that are answers to long-range questions lean on S1 (memory)
- Anchor tokens that need precise cross-referencing lean on S3 (attention)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class FusionGate(nn.Module):
    """
    Learned gating mechanism that combines three representation streams.

    Architecture:
        Concatenate [s1, s2, s3] -> Linear -> Softmax -> weighted sum

    The softmax ensures the three weights sum to 1, which:
    - Makes training stable (no exploding contributions)
    - Makes the gate interpretable (you can inspect which stratum dominates)
    - Prevents the model from just adding all three (which loses the routing benefit)
    """

    def __init__(
        self,
        d_model: int = 768,
        n_strata: int = 3,
        temperature: float = 1.0,
    ):
        super().__init__()
        self.d_model = d_model
        self.n_strata = n_strata
        self.temperature = temperature

        # Gate network: takes concatenated strata, outputs n_strata weights
        self.gate = nn.Sequential(
            nn.Linear(d_model * n_strata, d_model),
            nn.GELU(),
            nn.Linear(d_model, n_strata),
        )

        self.ln = nn.LayerNorm(d_model)

    def forward(
        self,
        s1_memory: torch.Tensor,
        s2_mamba: torch.Tensor,
        s3_attention: torch.Tensor,
    ) -> dict:
        """
        Fuse three strata into a single representation.

        Args:
            s1_memory: (batch, seq_len, d_model) — episodic memory output
            s2_mamba: (batch, seq_len, d_model) — Mamba hidden states
            s3_attention: (batch, seq_len, d_model) — anchor attention output

        Returns:
            dict with:
                - output: (batch, seq_len, d_model) fused representation
                - gate_weights: (batch, seq_len, 3) per-token stratum weights
        """
        # Concatenate all three strata
        combined = torch.cat([s1_memory, s2_mamba, s3_attention], dim=-1)  # (batch, seq, 3*d)

        # Compute gate weights
        gate_logits = self.gate(combined)  # (batch, seq_len, n_strata)
        gate_weights = F.softmax(gate_logits / self.temperature, dim=-1)  # (batch, seq_len, 3)

        # Weighted sum
        # Stack strata: (batch, seq_len, n_strata, d_model)
        stacked = torch.stack([s1_memory, s2_mamba, s3_attention], dim=2)

        # Apply weights: (batch, seq_len, n_strata, 1) * (batch, seq_len, n_strata, d_model)
        weighted = gate_weights.unsqueeze(-1) * stacked
        output = weighted.sum(dim=2)  # (batch, seq_len, d_model)

        output = self.ln(output)

        return {
            "output": output,
            "gate_weights": gate_weights,
        }
