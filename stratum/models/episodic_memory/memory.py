"""
Episodic Memory — Stratum 1.

A fixed-size differentiable memory store that receives compressed
summaries as Mamba processes chunks of tokens. Unlike RAG (retrieve
from a vector database), this is part of the forward pass — memory
vectors get gradients during training, so the model learns what's
worth remembering.

This is how STRATUM beats "lost in the middle": important information
from position 5M doesn't decay — it gets written to episodic memory
and stays accessible at position 50M.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional


class EpisodicMemory(nn.Module):
    """
    Fixed-size differentiable memory with learned read/write operations.

    Architecture:
        - Memory bank: (n_slots, d_model) — fixed number of slots
        - Write head: projects chunk summary -> memory update
        - Read head: attention over memory slots given current hidden state
        - Erase gate: decides what to forget before writing

    Inspired by Differentiable Neural Computers (Graves et al.)
    and Titans (Google, 2024), but simplified for SSM integration.
    """

    def __init__(
        self,
        d_model: int = 768,
        n_slots: int = 128,
        chunk_size: int = 512,
    ):
        super().__init__()
        self.d_model = d_model
        self.n_slots = n_slots
        self.chunk_size = chunk_size

        # Memory bank — initialized as learnable parameter
        self.memory_init = nn.Parameter(torch.randn(1, n_slots, d_model) * 0.02)

        # Write head: compresses a chunk into a write vector
        self.write_proj = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.GELU(),
            nn.Linear(d_model, d_model),
        )

        # Write address: decides WHICH slot to write to
        self.write_address = nn.Linear(d_model, n_slots)

        # Erase gate: decides how much of existing memory to keep
        self.erase_gate = nn.Sequential(
            nn.Linear(d_model, n_slots),
            nn.Sigmoid(),
        )

        # Read head: attention over memory given query
        self.read_query = nn.Linear(d_model, d_model)
        self.read_key = nn.Linear(d_model, d_model)
        self.read_value = nn.Linear(d_model, d_model)

        self.ln = nn.LayerNorm(d_model)

    def init_memory(self, batch_size: int, device: torch.device) -> torch.Tensor:
        """Initialize memory for a new sequence."""
        return self.memory_init.expand(batch_size, -1, -1).clone()

    def write(
        self,
        memory: torch.Tensor,
        chunk_hidden: torch.Tensor,
    ) -> torch.Tensor:
        """
        Write a chunk summary to memory.

        Args:
            memory: (batch, n_slots, d_model) current memory state
            chunk_hidden: (batch, chunk_size, d_model) hidden states for this chunk

        Returns:
            updated_memory: (batch, n_slots, d_model)
        """
        # Compress chunk to single vector via mean pooling
        chunk_summary = chunk_hidden.mean(dim=1)  # (batch, d_model)

        # Compute write vector
        write_vec = self.write_proj(chunk_summary)  # (batch, d_model)

        # Compute write address (soft attention over slots)
        address = F.softmax(self.write_address(chunk_summary), dim=-1)  # (batch, n_slots)

        # Compute erase signal
        erase = self.erase_gate(chunk_summary)  # (batch, n_slots)

        # Erase old content: memory = memory * (1 - erase * address)
        erase_matrix = 1.0 - erase.unsqueeze(-1) * address.unsqueeze(-1)
        memory = memory * erase_matrix

        # Write new content: memory += address * write_vec
        write_matrix = address.unsqueeze(-1) * write_vec.unsqueeze(1)  # (batch, n_slots, d_model)
        memory = memory + write_matrix

        return memory

    def read(
        self,
        memory: torch.Tensor,
        query_hidden: torch.Tensor,
    ) -> torch.Tensor:
        """
        Read from memory using attention.

        Args:
            memory: (batch, n_slots, d_model) current memory state
            query_hidden: (batch, seq_len, d_model) positions requesting memory

        Returns:
            read_output: (batch, seq_len, d_model) memory contribution per position
        """
        memory = self.ln(memory)

        # Project queries and memory keys/values
        q = self.read_query(query_hidden)  # (batch, seq_len, d_model)
        k = self.read_key(memory)          # (batch, n_slots, d_model)
        v = self.read_value(memory)        # (batch, n_slots, d_model)

        # Attention: (batch, seq_len, n_slots)
        scale = self.d_model ** 0.5
        attn = torch.matmul(q, k.transpose(-2, -1)) / scale
        attn = F.softmax(attn, dim=-1)

        # Read: (batch, seq_len, d_model)
        read_output = torch.matmul(attn, v)

        return read_output

    def forward(
        self,
        hidden_states: torch.Tensor,
        memory: Optional[torch.Tensor] = None,
    ) -> dict:
        """
        Process a sequence: write chunks to memory, read memory at each position.

        Args:
            hidden_states: (batch, seq_len, d_model)
            memory: optional pre-existing memory state

        Returns:
            dict with:
                - output: (batch, seq_len, d_model) memory-augmented representation
                - memory: (batch, n_slots, d_model) updated memory state
        """
        batch_size, seq_len, d_model = hidden_states.shape
        device = hidden_states.device

        if memory is None:
            memory = self.init_memory(batch_size, device)

        # Write chunks to memory
        n_chunks = seq_len // self.chunk_size
        for i in range(n_chunks):
            start = i * self.chunk_size
            end = start + self.chunk_size
            chunk = hidden_states[:, start:end, :]
            memory = self.write(memory, chunk)

        # Handle remaining tokens
        remainder = seq_len % self.chunk_size
        if remainder > 0:
            chunk = hidden_states[:, -remainder:, :]
            memory = self.write(memory, chunk)

        # Read from memory at every position
        output = self.read(memory, hidden_states)

        return {
            "output": output,
            "memory": memory,
        }
