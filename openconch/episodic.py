"""
Episodic Memory Store — fixed-size, compressed, temporally-aware.

Unlike a vector database that grows forever, the episodic store has
a fixed number of slots. When full, the least relevant memory gets
evicted. Relevance is determined by the Mamba temporal scorer, which
understands WHEN memories matter — not just IF they match.

Think of it like human memory: you don't remember every meal you've
ever eaten. But you remember your wedding dinner, your first date,
the time you got food poisoning. The episodic store learns what to
keep and what to let go.
"""

import json
import os
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from openconch.utils import generate_id, now_timestamp, cosine_similarity


@dataclass
class EpisodicSlot:
    """A single slot in the episodic memory bank."""
    id: str
    content: str
    embedding: List[float]
    salience: float
    created_at: float
    last_accessed_at: float
    access_count: int = 0
    metadata: dict = field(default_factory=dict)


class EpisodicStore:
    """
    Fixed-size memory store with learned eviction.

    Architecture:
    - Fixed number of slots (default 256)
    - Each slot holds: content, embedding, salience score, temporal metadata
    - On write: if full, evict the slot with lowest relevance score
    - On read: score all slots against query using embedding similarity
      AND temporal relevance (via Mamba when available)
    - Relevance = semantic_similarity * temporal_relevance
    """

    def __init__(
        self,
        n_slots: int = 256,
        persist_path: Optional[str] = None,
    ):
        self.n_slots = n_slots
        self.persist_path = persist_path
        self.slots: Dict[str, EpisodicSlot] = {}

        # Load from disk if available
        if persist_path and os.path.exists(persist_path):
            self._load()

    def write(
        self,
        content: str,
        embedding: List[float],
        salience: float,
        metadata: Optional[dict] = None,
    ) -> Tuple[str, Optional[str]]:
        """
        Write a memory to the episodic store.

        If the store is full, evicts the least relevant slot.

        Args:
            content: Memory text
            embedding: Vector embedding
            salience: Salience score from scorer (0-1)
            metadata: Optional metadata dict

        Returns:
            Tuple of (new_memory_id, evicted_memory_id or None)
        """
        memory_id = generate_id()
        now = now_timestamp()

        slot = EpisodicSlot(
            id=memory_id,
            content=content,
            embedding=embedding,
            salience=salience,
            created_at=now,
            last_accessed_at=now,
            access_count=0,
            metadata=metadata or {},
        )

        evicted_id = None

        # Evict if full
        if len(self.slots) >= self.n_slots:
            evicted_id = self._evict()

        self.slots[memory_id] = slot
        self._save()

        return memory_id, evicted_id

    def read(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        temporal_scores: Optional[Dict[str, float]] = None,
    ) -> List[Dict]:
        """
        Retrieve memories most relevant to the query.

        Combines embedding similarity with temporal relevance.
        If temporal_scores are provided (from Mamba scorer), they're
        used directly. Otherwise, all memories are scored equally
        on the temporal axis.

        Args:
            query_embedding: Query vector embedding
            top_k: Number of results to return
            temporal_scores: Optional dict of memory_id -> temporal relevance (from Mamba)

        Returns:
            List of dicts with memory content, score, and metadata
        """
        if not self.slots:
            return []

        scored = []
        for mem_id, slot in self.slots.items():
            # Semantic similarity
            sim = cosine_similarity(query_embedding, slot.embedding)

            # Temporal relevance from Mamba (or 1.0 if not available)
            temporal = temporal_scores.get(mem_id, 1.0) if temporal_scores else 1.0

            # Combined score: semantic * temporal * salience
            combined = sim * 0.5 + temporal * 0.3 + slot.salience * 0.2

            scored.append((mem_id, combined, sim, temporal))

        # Sort by combined score
        scored.sort(key=lambda x: x[1], reverse=True)

        # Update access metadata for returned results
        results = []
        for mem_id, combined, sim, temporal in scored[:top_k]:
            slot = self.slots[mem_id]
            slot.last_accessed_at = now_timestamp()
            slot.access_count += 1

            results.append({
                "id": slot.id,
                "content": slot.content,
                "score": combined,
                "semantic_similarity": sim,
                "temporal_relevance": temporal,
                "salience": slot.salience,
                "created_at": slot.created_at,
                "access_count": slot.access_count,
                "metadata": slot.metadata,
            })

        self._save()
        return results

    def update(self, memory_id: str, content: str, embedding: List[float], salience: float):
        """Update an existing memory's content."""
        if memory_id in self.slots:
            slot = self.slots[memory_id]
            slot.content = content
            slot.embedding = embedding
            slot.salience = salience
            slot.last_accessed_at = now_timestamp()
            self._save()

    def delete(self, memory_id: str) -> bool:
        """Delete a memory from the episodic store."""
        if memory_id in self.slots:
            del self.slots[memory_id]
            self._save()
            return True
        return False

    def get(self, memory_id: str) -> Optional[Dict]:
        """Get a specific memory by ID."""
        slot = self.slots.get(memory_id)
        if slot:
            return {
                "id": slot.id,
                "content": slot.content,
                "salience": slot.salience,
                "created_at": slot.created_at,
                "access_count": slot.access_count,
                "metadata": slot.metadata,
            }
        return None

    def get_all(self) -> List[Dict]:
        """Get all memories in the store."""
        return [
            {
                "id": s.id,
                "content": s.content,
                "salience": s.salience,
                "created_at": s.created_at,
                "access_count": s.access_count,
                "metadata": s.metadata,
            }
            for s in sorted(self.slots.values(), key=lambda s: s.created_at, reverse=True)
        ]

    def _evict(self) -> str:
        """
        Evict the least relevant memory to make room.

        Eviction priority (lowest score gets evicted):
        - Low salience
        - Old and never accessed
        - Low access count
        """
        if not self.slots:
            return ""

        # Score each slot for eviction
        eviction_candidates = []
        for mem_id, slot in self.slots.items():
            # Lower score = more likely to evict
            eviction_score = (
                slot.salience * 0.4
                + min(slot.access_count / 10.0, 1.0) * 0.4
                + 0.2  # Base survival score
            )
            eviction_candidates.append((mem_id, eviction_score))

        # Evict the lowest-scoring slot
        eviction_candidates.sort(key=lambda x: x[1])
        evict_id = eviction_candidates[0][0]
        del self.slots[evict_id]

        return evict_id

    def _save(self):
        """Persist to disk."""
        if not self.persist_path:
            return
        os.makedirs(os.path.dirname(self.persist_path) if os.path.dirname(self.persist_path) else ".", exist_ok=True)
        data = {}
        for mem_id, slot in self.slots.items():
            data[mem_id] = {
                "id": slot.id,
                "content": slot.content,
                "embedding": slot.embedding,
                "salience": slot.salience,
                "created_at": slot.created_at,
                "last_accessed_at": slot.last_accessed_at,
                "access_count": slot.access_count,
                "metadata": slot.metadata,
            }
        with open(self.persist_path, "w") as f:
            json.dump(data, f)

    def _load(self):
        """Load from disk."""
        if not self.persist_path or not os.path.exists(self.persist_path):
            return
        with open(self.persist_path) as f:
            data = json.load(f)
        for mem_id, d in data.items():
            self.slots[mem_id] = EpisodicSlot(**d)

    @property
    def size(self) -> int:
        return len(self.slots)

    @property
    def capacity(self) -> int:
        return self.n_slots

    @property
    def utilization(self) -> float:
        return self.size / self.capacity
