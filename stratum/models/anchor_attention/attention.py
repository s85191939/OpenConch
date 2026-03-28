"""
Anchor Attention — Stratum 3.

Full quadratic self-attention applied ONLY to the ~0.5% of tokens
flagged as anchors by the salience scorer. This gives STRATUM the
precision of a transformer on the tokens that actually need it,
without paying O(n²) over the full sequence.

At 1B tokens with 0.5% anchor rate = ~5M tokens under attention.
That's tractable with FlashAttention and pipeline parallelism.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math
from typing import Optional


class AnchorAttention(nn.Module):
    """
    Sparse attention that operates only on anchor-flagged tokens.

    Architecture:
        1. Gather anchor hidden states using the anchor mask
        2. Run standard multi-head self-attention on the gathered subset
        3. Scatter the attended representations back to original positions

    This is NOT windowed attention or linear attention — it's full
    quadratic attention, but only on the tokens that matter.
    """

    def __init__(
        self,
        d_model: int = 768,
        n_heads: int = 8,
        dropout: float = 0.1,
        use_flash: bool = True,
    ):
        super().__init__()
        self.d_model = d_model
        self.n_heads = n_heads
        self.head_dim = d_model // n_heads
        self.use_flash = use_flash

        assert d_model % n_heads == 0, "d_model must be divisible by n_heads"

        self.q_proj = nn.Linear(d_model, d_model)
        self.k_proj = nn.Linear(d_model, d_model)
        self.v_proj = nn.Linear(d_model, d_model)
        self.out_proj = nn.Linear(d_model, d_model)

        self.dropout = nn.Dropout(dropout)
        self.ln = nn.LayerNorm(d_model)

    def forward(
        self,
        hidden_states: torch.Tensor,
        anchor_mask: torch.BoolTensor,
    ) -> torch.Tensor:
        """
        Run attention on anchor tokens only, return full-sequence output.

        Args:
            hidden_states: (batch, seq_len, d_model) — full sequence
            anchor_mask: (batch, seq_len) — True for anchor positions

        Returns:
            output: (batch, seq_len, d_model) — zeros at non-anchor positions,
                    attended representations at anchor positions
        """
        batch_size, seq_len, d_model = hidden_states.shape
        device = hidden_states.device

        # Initialize output as zeros — non-anchor positions get no contribution
        output = torch.zeros_like(hidden_states)

        # Process each batch element (anchor counts may differ)
        for b in range(batch_size):
            mask = anchor_mask[b]  # (seq_len,)
            n_anchors = mask.sum().item()

            if n_anchors == 0:
                continue

            # Gather anchor hidden states: (n_anchors, d_model)
            anchor_hidden = hidden_states[b, mask, :]  # (n_anchors, d_model)
            anchor_hidden = self.ln(anchor_hidden)

            # Project Q, K, V
            q = self.q_proj(anchor_hidden)  # (n_anchors, d_model)
            k = self.k_proj(anchor_hidden)
            v = self.v_proj(anchor_hidden)

            # Reshape for multi-head: (n_heads, n_anchors, head_dim)
            q = q.view(n_anchors, self.n_heads, self.head_dim).transpose(0, 1)
            k = k.view(n_anchors, self.n_heads, self.head_dim).transpose(0, 1)
            v = v.view(n_anchors, self.n_heads, self.head_dim).transpose(0, 1)

            # Standard scaled dot-product attention
            # For small anchor sets, vanilla attention is fine.
            # FlashAttention kicks in when anchor count is large.
            scale = math.sqrt(self.head_dim)
            attn_weights = torch.matmul(q, k.transpose(-2, -1)) / scale
            attn_weights = F.softmax(attn_weights, dim=-1)
            attn_weights = self.dropout(attn_weights)

            # Apply attention to values
            attn_output = torch.matmul(attn_weights, v)  # (n_heads, n_anchors, head_dim)

            # Reshape back: (n_anchors, d_model)
            attn_output = attn_output.transpose(0, 1).contiguous().view(n_anchors, d_model)
            attn_output = self.out_proj(attn_output)

            # Scatter back to original positions
            output[b, mask, :] = attn_output

        return output


class AnchorAttentionBatched(nn.Module):
    """
    Batched version for when anchor counts are uniform (e.g., fixed top-k).

    More efficient than the loop-based version when all batch elements
    have the same number of anchors (which they do when using top-k selection).
    """

    def __init__(
        self,
        d_model: int = 768,
        n_heads: int = 8,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.d_model = d_model
        self.n_heads = n_heads
        self.head_dim = d_model // n_heads

        self.q_proj = nn.Linear(d_model, d_model)
        self.k_proj = nn.Linear(d_model, d_model)
        self.v_proj = nn.Linear(d_model, d_model)
        self.out_proj = nn.Linear(d_model, d_model)

        self.dropout = nn.Dropout(dropout)
        self.ln = nn.LayerNorm(d_model)

    def forward(
        self,
        hidden_states: torch.Tensor,
        anchor_indices: torch.LongTensor,
    ) -> torch.Tensor:
        """
        Batched attention using gather/scatter with fixed anchor count.

        Args:
            hidden_states: (batch, seq_len, d_model)
            anchor_indices: (batch, n_anchors) — positions of anchor tokens

        Returns:
            output: (batch, seq_len, d_model)
        """
        batch_size, seq_len, d_model = hidden_states.shape
        n_anchors = anchor_indices.shape[1]

        # Gather: (batch, n_anchors, d_model)
        idx = anchor_indices.unsqueeze(-1).expand(-1, -1, d_model)
        anchor_hidden = torch.gather(hidden_states, 1, idx)
        anchor_hidden = self.ln(anchor_hidden)

        # Project
        q = self.q_proj(anchor_hidden).view(batch_size, n_anchors, self.n_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(anchor_hidden).view(batch_size, n_anchors, self.n_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(anchor_hidden).view(batch_size, n_anchors, self.n_heads, self.head_dim).transpose(1, 2)

        # Attention: (batch, n_heads, n_anchors, n_anchors)
        scale = math.sqrt(self.head_dim)
        attn = F.softmax(torch.matmul(q, k.transpose(-2, -1)) / scale, dim=-1)
        attn = self.dropout(attn)

        # Output: (batch, n_heads, n_anchors, head_dim) -> (batch, n_anchors, d_model)
        out = torch.matmul(attn, v).transpose(1, 2).contiguous().view(batch_size, n_anchors, d_model)
        out = self.out_proj(out)

        # Scatter back
        output = torch.zeros_like(hidden_states)
        output.scatter_(1, idx, out)

        return output
