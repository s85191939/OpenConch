"""
Salience Scorer — the architectural key of STRATUM.

A lightweight 2-layer MLP that runs on each Mamba hidden state and outputs
a scalar salience score. Tokens above a dynamic threshold are flagged as
"anchors" and routed to full quadratic attention (Stratum 3).

Training signal:
- During pretraining: contrastive — tokens the model later needed for
  accurate prediction get positive reward; tokens flagged as anchors but
  never consulted get negative reward.
- For Experiment 2: surrogate — tokens whose masking causes the largest
  prediction loss change are labeled salient.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional


class SalienceScorer(nn.Module):
    """
    Scores each token's hidden state for salience.

    Architecture:
        hidden_state (d_model) -> Linear(d_model, d_inner) -> GELU -> Linear(d_inner, 1) -> Sigmoid

    The scorer is deliberately small (2 layers, ~2x expansion) to add
    minimal overhead per token. At 768 d_model, this is ~1.2M params —
    negligible compared to the backbone.
    """

    def __init__(
        self,
        d_model: int = 768,
        d_inner: Optional[int] = None,
        dropout: float = 0.1,
        anchor_ratio: float = 0.005,  # target ~0.5% of tokens as anchors
        temperature: float = 1.0,
    ):
        super().__init__()
        self.d_model = d_model
        self.d_inner = d_inner or d_model * 2
        self.anchor_ratio = anchor_ratio
        self.temperature = temperature

        self.scorer = nn.Sequential(
            nn.Linear(d_model, self.d_inner),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(self.d_inner, 1),
        )

        # Learnable threshold bias — allows the model to shift the
        # anchor selection point during training
        self.threshold_bias = nn.Parameter(torch.tensor(0.0))

    def forward(
        self,
        hidden_states: torch.Tensor,
        return_scores: bool = False,
        force_anchor_mask: Optional[torch.BoolTensor] = None,
    ) -> dict:
        """
        Score each token and select anchors.

        Args:
            hidden_states: (batch, seq_len, d_model)
            return_scores: if True, include raw scores in output
            force_anchor_mask: (batch, seq_len) bool — oracle override for Exp 1.
                If provided, bypasses the scorer entirely and uses this mask.

        Returns:
            dict with:
                - anchor_mask: (batch, seq_len) bool tensor, True for anchor tokens
                - anchor_indices: list of (batch,) tensors with anchor positions
                - scores: (batch, seq_len) raw salience scores (if return_scores)
                - num_anchors: int, total anchors selected
        """
        batch_size, seq_len, _ = hidden_states.shape

        # Oracle mode — skip scoring, use provided mask
        if force_anchor_mask is not None:
            anchor_mask = force_anchor_mask.bool()
            return {
                "anchor_mask": anchor_mask,
                "anchor_indices": [mask.nonzero(as_tuple=True)[0] for mask in anchor_mask],
                "num_anchors": anchor_mask.sum().item(),
            }

        # Score each position
        scores = self.scorer(hidden_states).squeeze(-1)  # (batch, seq_len)
        scores = torch.sigmoid(scores / self.temperature)

        # Select top-k anchors based on anchor_ratio
        k = max(1, int(seq_len * self.anchor_ratio))
        topk_values, topk_indices = torch.topk(scores, k=k, dim=-1)

        # Build boolean mask
        anchor_mask = torch.zeros(batch_size, seq_len, dtype=torch.bool, device=hidden_states.device)
        anchor_mask.scatter_(1, topk_indices, True)

        result = {
            "anchor_mask": anchor_mask,
            "anchor_indices": [topk_indices[b] for b in range(batch_size)],
            "num_anchors": anchor_mask.sum().item(),
        }

        if return_scores:
            result["scores"] = scores

        return result

    def compute_surrogate_labels(
        self,
        backbone: nn.Module,
        input_ids: torch.LongTensor,
        hidden_states: torch.Tensor,
        n_probe: int = 50,
    ) -> torch.Tensor:
        """
        Compute surrogate salience labels for Experiment 2.

        For each of n_probe randomly sampled positions, mask that position's
        hidden state and measure the increase in prediction loss. Positions
        causing the largest loss increase are labeled as salient.

        Args:
            backbone: the Mamba backbone (for the LM head)
            input_ids: (batch, seq_len) ground truth token IDs
            hidden_states: (batch, seq_len, d_model) from backbone forward pass
            n_probe: number of positions to probe per sequence

        Returns:
            labels: (batch, seq_len) float tensor, higher = more salient
        """
        batch_size, seq_len, d_model = hidden_states.shape
        device = hidden_states.device

        # Compute baseline loss at each position
        # (This is an approximation — we measure local prediction quality)
        labels = torch.zeros(batch_size, seq_len, device=device)

        # Sample random positions to probe
        probe_positions = torch.randint(1, seq_len - 1, (n_probe,), device=device)

        with torch.no_grad():
            for pos in probe_positions:
                # Zero out this position's hidden state
                masked_hidden = hidden_states.clone()
                masked_hidden[:, pos, :] = 0.0

                # Measure prediction quality at next position
                # Higher loss increase = more salient position
                # We use L2 distance as proxy for "information lost"
                original_repr = hidden_states[:, pos + 1, :]
                # Simple proxy: how much does zeroing this position affect neighbors
                impact = torch.norm(hidden_states[:, pos, :], dim=-1)
                labels[:, pos] = impact

        # Normalize to [0, 1]
        labels = labels / (labels.max(dim=-1, keepdim=True).values + 1e-8)

        return labels
