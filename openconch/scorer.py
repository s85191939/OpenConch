"""
Salience Scorer — decides what's worth remembering.

Two modes:
1. Heuristic (CPU, no dependencies): keyword density, entity detection,
   novelty vs existing memories. Fast fallback.
2. Mamba (GPU, learned): STRATUM's salience scorer trained to predict
   which tokens/memories the model will actually need later. Also handles
   temporal relevance — the model learns WHEN a memory matters, not just
   IF it matches. No hardcoded decay curves.

The Mamba scorer processes the full temporal sequence of memories
(ordered by time) and learns which ones are relevant to the current
query. A memory from 6 months ago that's directly relevant scores
higher than a memory from 5 minutes ago that's noise. The model
learns this from data, not from an exponential decay formula.
"""

import re
import math
from typing import List, Dict, Optional, Tuple
from openconch.utils import now_timestamp


class HeuristicScorer:
    """
    CPU-based salience scoring using simple heuristics.

    Scores memories on a 0-1 scale based on:
    - Entity density (named entities, numbers, dates)
    - Specificity (concrete details vs vague statements)
    - Novelty (how different from existing memories)
    - Length (very short = low info, very long = might need compression)
    """

    # Patterns that indicate high-salience content
    ENTITY_PATTERNS = [
        r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)+\b',  # Proper nouns (multi-word)
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',    # Dates
        r'\b\d+(?:\.\d+)?%\b',                     # Percentages
        r'\$\d+(?:,\d{3})*(?:\.\d{2})?\b',         # Dollar amounts
        r'\b\d{3,}\b',                              # Large numbers
        r'\b[A-Z]{2,}\b',                           # Acronyms
    ]

    # Words that indicate factual/important content
    SALIENCE_KEYWORDS = {
        "always", "never", "prefer", "hate", "love", "allergic",
        "birthday", "password", "address", "phone", "email",
        "deadline", "meeting", "appointment", "important", "critical",
        "remember", "don't forget", "key", "essential", "must",
    }

    def score(self, text: str, existing_memories: Optional[List[str]] = None) -> float:
        """
        Score a text for salience.

        Returns float between 0 (not worth remembering) and 1 (critical).
        """
        scores = []

        # Entity density
        entity_count = sum(len(re.findall(p, text)) for p in self.ENTITY_PATTERNS)
        word_count = max(len(text.split()), 1)
        entity_score = min(1.0, entity_count / max(word_count * 0.1, 1))
        scores.append(entity_score * 0.3)

        # Keyword salience
        text_lower = text.lower()
        keyword_hits = sum(1 for kw in self.SALIENCE_KEYWORDS if kw in text_lower)
        keyword_score = min(1.0, keyword_hits / 3.0)
        scores.append(keyword_score * 0.3)

        # Specificity (concrete details vs vague)
        specificity = min(1.0, len(text) / 200.0)  # Longer = more specific, up to a point
        scores.append(specificity * 0.2)

        # Novelty (if we have existing memories to compare against)
        if existing_memories:
            novelty = self._compute_novelty(text, existing_memories)
            scores.append(novelty * 0.2)
        else:
            scores.append(0.15)  # Default medium novelty

        return min(1.0, sum(scores))

    def _compute_novelty(self, text: str, existing: List[str]) -> float:
        """How different is this text from existing memories? (word overlap)"""
        text_words = set(text.lower().split())
        if not text_words:
            return 0.0

        max_overlap = 0.0
        for mem in existing[-50:]:  # Only check recent memories
            mem_words = set(mem.lower().split())
            if not mem_words:
                continue
            overlap = len(text_words & mem_words) / len(text_words | mem_words)
            max_overlap = max(max_overlap, overlap)

        # High overlap = low novelty
        return 1.0 - max_overlap


class MambaTemporalScorer:
    """
    Mamba-based scorer that learns temporal relevance from data.

    Instead of hardcoded decay: the scorer processes the full sequence
    of memories (oldest → newest) through Mamba, which maintains a
    compressed state of the entire memory history. When you query,
    it scores each memory based on:
    - Semantic relevance to the query
    - Temporal context (what came before/after this memory)
    - Usage patterns (memories accessed often get reinforced)
    - Causal chains (memory A led to memory B, so A stays relevant)

    The key insight: Mamba's hidden state IS the temporal model.
    It processes memories in chronological order and its state at
    each position encodes "everything the agent has experienced so
    far." The scorer MLP then asks "given this temporal context,
    how relevant is this memory to the current query?"

    This requires GPU and trained weights. Falls back to HeuristicScorer
    if unavailable.
    """

    def __init__(self, model_path: Optional[str] = None, device: str = "cuda"):
        self.device = device
        self.model_path = model_path
        self._backbone = None
        self._scorer = None
        self._loaded = False

    def _load(self):
        """Lazy-load Mamba backbone and scorer."""
        if self._loaded:
            return

        try:
            import torch
            import sys
            sys.path.insert(0, "stratum")
            from stratum.models.mamba_backbone import MambaBackbone
            from stratum.models.salience_scorer import SalienceScorer

            self._backbone = MambaBackbone.from_pretrained(
                "state-spaces/mamba-130m", freeze=True
            ).to(self.device)

            self._scorer = SalienceScorer(
                d_model=768,
                d_inner=1536,
                anchor_ratio=0.005,
            ).to(self.device)

            # Load trained weights if available
            if self.model_path:
                state_dict = torch.load(self.model_path, map_location=self.device)
                self._scorer.load_state_dict(state_dict)

            self._loaded = True

        except (ImportError, RuntimeError) as e:
            print(f"[OpenConch] Mamba scorer unavailable ({e}), using heuristic fallback")
            self._loaded = False

    def score_temporal_batch(
        self,
        memory_texts: List[str],
        memory_timestamps: List[float],
        query: str,
        tokenizer=None,
    ) -> List[float]:
        """
        Score a batch of memories for temporal relevance to a query.

        Processes memories in chronological order through Mamba, then
        scores each memory's hidden state against the query.

        Args:
            memory_texts: List of memory contents, chronologically ordered
            memory_timestamps: Unix timestamps for each memory
            query: The current query to score against

        Returns:
            List of salience scores (0-1) for each memory
        """
        self._load()

        if not self._loaded:
            # Fallback to heuristic
            h = HeuristicScorer()
            return [h.score(text) for text in memory_texts]

        import torch

        if tokenizer is None:
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-neox-20b")

        # Build temporal sequence: memories in chronological order
        # Each memory is prefixed with a relative time marker
        temporal_sequence = ""
        base_time = memory_timestamps[0] if memory_timestamps else now_timestamp()

        for text, ts in zip(memory_texts, memory_timestamps):
            hours_ago = (now_timestamp() - ts) / 3600.0
            temporal_sequence += f" [T-{hours_ago:.1f}h] {text}"

        # Add query at the end
        temporal_sequence += f" [QUERY] {query}"

        # Tokenize and run through Mamba
        input_ids = tokenizer.encode(temporal_sequence, return_tensors="pt").to(self.device)

        with torch.no_grad():
            result = self._backbone(input_ids)
            hidden = result["hidden_states"]

            # Score each position
            scorer_out = self._scorer(hidden, return_scores=True)
            scores = scorer_out["scores"][0]  # (seq_len,)

        # Map token scores back to memory scores
        # Find the start token of each memory in the sequence
        memory_scores = []
        current_pos = 0
        for text in memory_texts:
            mem_tokens = tokenizer.encode(text, add_special_tokens=False)
            # Find this memory's position in the sequence
            mem_start = temporal_sequence.find(text)
            if mem_start >= 0:
                token_pos = len(tokenizer.encode(temporal_sequence[:mem_start], add_special_tokens=False))
                token_end = token_pos + len(mem_tokens)
                # Average score across this memory's tokens
                if token_end <= scores.shape[0]:
                    mem_score = scores[token_pos:token_end].mean().item()
                else:
                    mem_score = 0.5
            else:
                mem_score = 0.5
            memory_scores.append(mem_score)

        return memory_scores

    @property
    def is_available(self) -> bool:
        """Check if Mamba scorer can be loaded."""
        self._load()
        return self._loaded


class SalienceScorer:
    """
    Unified scorer that uses Mamba when available, heuristic when not.
    """

    def __init__(
        self,
        mode: str = "heuristic",
        mamba_model_path: Optional[str] = None,
        device: str = "cuda",
    ):
        self.mode = mode
        self.heuristic = HeuristicScorer()
        self._mamba = None

        if mode == "mamba":
            self._mamba = MambaTemporalScorer(
                model_path=mamba_model_path,
                device=device,
            )

    def score(self, text: str, existing_memories: Optional[List[str]] = None) -> float:
        """Score a single memory for salience."""
        return self.heuristic.score(text, existing_memories)

    def score_temporal(
        self,
        memories: List[Dict],
        query: str,
    ) -> List[float]:
        """
        Score memories with temporal context using Mamba.

        Falls back to heuristic if Mamba unavailable.

        Args:
            memories: List of dicts with 'content' and 'created_at' keys
            query: Current search query

        Returns:
            List of relevance scores (0-1)
        """
        if self._mamba and self._mamba.is_available:
            texts = [m["content"] for m in memories]
            timestamps = [m.get("created_at", now_timestamp()) for m in memories]
            return self._mamba.score_temporal_batch(texts, timestamps, query)
        else:
            # Heuristic fallback: score each memory independently
            return [self.heuristic.score(m["content"]) for m in memories]
