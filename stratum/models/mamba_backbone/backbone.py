"""
Mamba-2 backbone wrapper.

Loads a pretrained Mamba model (e.g., state-spaces/mamba-130m) and exposes
hidden states at each position for downstream use by the salience scorer
and episodic memory.
"""

import torch
import torch.nn as nn
from typing import Optional


class MambaBackbone(nn.Module):
    """
    Wraps a pretrained Mamba model to extract per-token hidden states.

    The backbone processes token sequences in linear time O(n) with constant
    memory per step (no KV cache). Hidden states are exposed for:
    - Salience scorer (decides which tokens become anchors)
    - Episodic memory (writes compressed summaries)
    - Direct output contribution via fusion gate
    """

    def __init__(
        self,
        model_name: str = "state-spaces/mamba-130m",
        d_model: int = 768,
        n_layer: int = 24,
        freeze: bool = False,
    ):
        super().__init__()
        self.d_model = d_model
        self.n_layer = n_layer
        self.model_name = model_name
        self._freeze = freeze

        # Lazy load — actual model loaded in from_pretrained()
        self.mamba = None
        self.embedding = None
        self.ln_f = None

    @classmethod
    def from_pretrained(cls, model_name: str = "state-spaces/mamba-130m", freeze: bool = False):
        """Load a pretrained Mamba model from HuggingFace."""
        from mamba_ssm.models.mixer_seq_simple import MambaLMHeadModel

        instance = cls(model_name=model_name, freeze=freeze)

        # Load the full pretrained model
        pretrained = MambaLMHeadModel.from_pretrained(model_name, device="cuda", dtype=torch.float16)

        instance.mamba = pretrained.backbone
        instance.d_model = pretrained.backbone.layers[0].mixer.d_model
        instance.n_layer = len(pretrained.backbone.layers)

        # Extract embedding and final layernorm
        instance.embedding = pretrained.backbone.embedding
        instance.ln_f = pretrained.backbone.norm_f

        if freeze:
            for param in instance.parameters():
                param.requires_grad = False

        return instance

    @classmethod
    def from_config(cls, d_model: int = 768, n_layer: int = 24, vocab_size: int = 50280):
        """Create a fresh (untrained) Mamba backbone from config."""
        from mamba_ssm.models.mixer_seq_simple import MambaLMHeadModel

        instance = cls(d_model=d_model, n_layer=n_layer)

        # Create model from scratch
        from mamba_ssm.models.config_mamba import MambaConfig
        config = MambaConfig(
            d_model=d_model,
            n_layer=n_layer,
            vocab_size=vocab_size,
        )
        model = MambaLMHeadModel(config, device="cuda", dtype=torch.float16)

        instance.mamba = model.backbone
        instance.embedding = model.backbone.embedding
        instance.ln_f = model.backbone.norm_f

        return instance

    def forward(
        self,
        input_ids: torch.LongTensor,
        return_all_hidden: bool = False,
    ) -> dict:
        """
        Process token IDs through Mamba and return hidden states.

        Args:
            input_ids: (batch, seq_len) token IDs
            return_all_hidden: if True, return hidden states from every layer

        Returns:
            dict with:
                - hidden_states: (batch, seq_len, d_model) final layer hidden states
                - all_hidden: list of (batch, seq_len, d_model) per layer (if requested)
        """
        # Embed tokens
        hidden = self.embedding(input_ids)

        all_hidden = [] if return_all_hidden else None

        # Run through each Mamba layer
        residual = None
        for layer in self.mamba.layers:
            hidden, residual = layer(hidden, residual)
            if return_all_hidden:
                all_hidden.append(hidden)

        # Final layernorm
        hidden = self.ln_f(hidden if residual is None else hidden + residual)

        result = {"hidden_states": hidden}
        if return_all_hidden:
            result["all_hidden"] = all_hidden

        return result

    def get_hidden_size(self) -> int:
        return self.d_model
