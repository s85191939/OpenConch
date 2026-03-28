"""
Memory Router — orchestrates where memories go and how they're retrieved.

The router is the brain of OpenConch. It decides:
- On ADD: which store(s) to write to based on salience
- On SEARCH: how to query both stores and fuse results
- On UPDATE: whether to promote/demote memories between stores

Routing decisions:
    Salience >= 0.7 (HIGH)  → Episodic + Vector (dual storage, never lost)
    Salience 0.2-0.7 (MED)  → Vector only (standard retrieval)
    Salience < 0.2 (LOW)    → Compressed or dropped (noise)
"""

from typing import List, Dict, Optional, Tuple
from openconch.scorer import SalienceScorer
from openconch.episodic import EpisodicStore
from openconch.vector_store import VectorStore
from openconch.embeddings import EmbeddingEngine
from openconch.history import HistoryStore
from openconch.config import OpenConchConfig
from openconch.utils import generate_id, now_timestamp


class MemoryRouter:
    """
    Routes memory operations to the appropriate store(s).
    """

    def __init__(self, config: OpenConchConfig):
        self.config = config

        # Initialize components
        self.embedder = EmbeddingEngine(model_name=config.embedding_model)
        self.scorer = SalienceScorer(
            mode=config.salience_mode,
            device="cuda" if config.salience_mode == "mamba" else "cpu",
        )
        self.vector_store = VectorStore(
            backend=config.vector_store,
            collection_name=config.collection_name,
            persist_directory=config.persist_directory,
            qdrant_url=config.qdrant_url,
        )
        self.history = HistoryStore(db_path=config.history_db_path)

        # Episodic store (optional, requires GPU for full power)
        self.episodic_store = None
        if config.episodic_enabled:
            self.episodic_store = EpisodicStore(
                n_slots=config.episodic_slots,
                persist_path=f"{config.persist_directory}/episodic.json",
            )

    def add(
        self,
        content: str,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Dict:
        """
        Add a memory. Routes to appropriate store(s) based on salience.

        Returns dict with memory_id, salience, and storage tier.
        """
        # Generate embedding
        embedding = self.embedder.embed(content)

        # Score salience
        existing_contents = self._get_recent_contents(limit=50)
        salience = self.scorer.score(content, existing_contents)

        # Build metadata
        meta = metadata or {}
        if user_id:
            meta["user_id"] = user_id
        if agent_id:
            meta["agent_id"] = agent_id
        if session_id:
            meta["session_id"] = session_id
        meta["salience"] = salience
        meta["created_at"] = now_timestamp()

        memory_id = generate_id()
        tier = "dropped"
        evicted_id = None

        if salience >= self.config.salience_threshold_high:
            # HIGH salience → both stores
            tier = "episodic+vector"
            self.vector_store.add(memory_id, content, embedding, meta)

            if self.episodic_store:
                _, evicted_id = self.episodic_store.write(
                    content, embedding, salience, meta
                )

        elif salience >= self.config.salience_threshold_low:
            # MEDIUM salience → vector only
            tier = "vector"
            self.vector_store.add(memory_id, content, embedding, meta)

        else:
            # LOW salience → dropped (noise)
            tier = "dropped"

        # Record in history
        self.history.record(
            memory_id=memory_id,
            action="add",
            new_content=content,
            metadata={"tier": tier, "salience": salience, "evicted": evicted_id},
        )

        return {
            "id": memory_id,
            "content": content,
            "salience": salience,
            "tier": tier,
            "evicted_id": evicted_id,
        }

    def search(
        self,
        query: str,
        top_k: int = 10,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> List[Dict]:
        """
        Search memories across all stores, fuse and rerank results.

        The search pipeline:
        1. Embed the query
        2. Search vector store (semantic similarity)
        3. Search episodic store (semantic + temporal via Mamba)
        4. Fuse results, deduplicate, rerank
        """
        query_embedding = self.embedder.embed(query)

        # Build filters
        where_filters = filters or {}
        if user_id:
            where_filters["user_id"] = user_id
        if agent_id:
            where_filters["agent_id"] = agent_id
        if session_id:
            where_filters["session_id"] = session_id

        # Search vector store
        vector_results = self.vector_store.search(
            query_embedding,
            top_k=top_k * 2,  # Over-fetch for reranking
            filters=where_filters if where_filters else None,
        )

        # Search episodic store (with Mamba temporal scoring)
        episodic_results = []
        if self.episodic_store and self.episodic_store.size > 0:
            # Get temporal scores from Mamba if available
            temporal_scores = None
            if self.config.salience_mode == "mamba":
                all_memories = self.episodic_store.get_all()
                if all_memories:
                    scores = self.scorer.score_temporal(all_memories, query)
                    temporal_scores = {
                        m["id"]: s for m, s in zip(all_memories, scores)
                    }

            episodic_results = self.episodic_store.read(
                query_embedding,
                top_k=top_k,
                temporal_scores=temporal_scores,
            )

        # Fuse results
        fused = self._fuse_results(vector_results, episodic_results, top_k)

        return fused

    def update(
        self,
        memory_id: str,
        content: str,
    ) -> Dict:
        """Update a memory's content. Re-scores salience and may promote/demote."""
        embedding = self.embedder.embed(content)
        salience = self.scorer.score(content)

        # Update in vector store
        self.vector_store.update(memory_id, content, embedding, {"salience": salience})

        # Update in episodic store if present
        if self.episodic_store:
            self.episodic_store.update(memory_id, content, embedding, salience)

        self.history.record(
            memory_id=memory_id,
            action="update",
            new_content=content,
            metadata={"salience": salience},
        )

        return {"id": memory_id, "content": content, "salience": salience}

    def delete(self, memory_id: str) -> bool:
        """Delete a memory from all stores."""
        self.vector_store.delete(memory_id)
        if self.episodic_store:
            self.episodic_store.delete(memory_id)
        self.history.record(memory_id=memory_id, action="delete")
        return True

    def get(self, memory_id: str) -> Optional[Dict]:
        """Get a specific memory."""
        # Try vector store first
        result = self.vector_store.get(memory_id)
        if result:
            return result
        # Try episodic store
        if self.episodic_store:
            return self.episodic_store.get(memory_id)
        return None

    def get_all(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> List[Dict]:
        """Get all memories, optionally filtered by scope."""
        # For now, search with a broad query to get everything
        # A proper implementation would iterate the vector store
        results = self.vector_store.search(
            query_embedding=[0.0] * self.config.embedding_dim,
            top_k=1000,
            filters=self._build_scope_filter(user_id, agent_id, session_id),
        )
        return results

    def _fuse_results(
        self,
        vector_results: List[Dict],
        episodic_results: List[Dict],
        top_k: int,
    ) -> List[Dict]:
        """
        Fuse results from vector and episodic stores.

        Deduplicates by content similarity, boosts memories found in both stores.
        """
        seen_ids = set()
        fused = []

        # Add episodic results first (they have temporal context)
        for r in episodic_results:
            r["source"] = "episodic"
            r["score"] = r.get("score", 0) * 1.2  # Slight boost for episodic
            fused.append(r)
            seen_ids.add(r["id"])

        # Add vector results that aren't duplicates
        for r in vector_results:
            if r["id"] not in seen_ids:
                r["source"] = "vector"
                fused.append(r)
                seen_ids.add(r["id"])

        # Sort by score and return top_k
        fused.sort(key=lambda x: x.get("score", 0), reverse=True)
        return fused[:top_k]

    def _get_recent_contents(self, limit: int = 50) -> List[str]:
        """Get recent memory contents for novelty comparison."""
        results = self.vector_store.search(
            query_embedding=[0.0] * self.config.embedding_dim,
            top_k=limit,
        )
        return [r["content"] for r in results if r.get("content")]

    def _build_scope_filter(self, user_id, agent_id, session_id) -> Optional[dict]:
        """Build a filter dict from scope parameters."""
        f = {}
        if user_id:
            f["user_id"] = user_id
        if agent_id:
            f["agent_id"] = agent_id
        if session_id:
            f["session_id"] = session_id
        return f if f else None
