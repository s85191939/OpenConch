"""
Configuration for OpenConch.

Sensible defaults that work out of the box. Override what you need.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OpenConchConfig:
    """
    Configuration for an OpenConch Memory instance.

    Attributes:
        # Storage
        vector_store: Which vector backend to use ("chromadb" or "qdrant")
        collection_name: Name of the vector collection
        persist_directory: Where to store data on disk (ChromaDB)
        qdrant_url: Qdrant server URL (if using qdrant)

        # Episodic Memory
        episodic_enabled: Whether to use episodic memory (requires GPU for Mamba)
        episodic_slots: Number of memory slots in the episodic store
        episodic_chunk_size: Chunk size for episodic memory writes

        # Salience Scoring
        salience_mode: "heuristic" (CPU, fast) or "mamba" (GPU, learned)
        salience_threshold_high: Score above this → store in both episodic + vector
        salience_threshold_low: Score below this → compress or drop
        salience_anchor_ratio: Fraction of memories flagged as anchors

        # Temporal Memory
        temporal_decay_rate: How fast old memories lose relevance (0 = no decay, 1 = instant decay)
        temporal_half_life_hours: Hours until a memory's temporal weight drops to 0.5
        temporal_boost_on_access: How much accessing a memory boosts its temporal score

        # Embeddings
        embedding_model: Sentence-transformers model for embeddings
        embedding_dim: Dimension of embedding vectors

        # LLM
        llm_model: Claude model for fact extraction
        llm_api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)

        # History
        history_db_path: SQLite database for memory change history
    """

    # Storage
    vector_store: str = "chromadb"
    collection_name: str = "openconch_memories"
    persist_directory: str = ".openconch"
    qdrant_url: Optional[str] = None

    # Episodic Memory
    episodic_enabled: bool = False  # Off by default (requires GPU)
    episodic_slots: int = 256
    episodic_chunk_size: int = 512

    # Salience Scoring
    salience_mode: str = "heuristic"  # "heuristic" or "mamba"
    salience_threshold_high: float = 0.7
    salience_threshold_low: float = 0.2
    salience_anchor_ratio: float = 0.005

    # Temporal Memory
    temporal_decay_rate: float = 0.1
    temporal_half_life_hours: float = 168.0  # 1 week
    temporal_boost_on_access: float = 0.3

    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384

    # LLM
    llm_model: str = "claude-sonnet-4-20250514"
    llm_api_key: Optional[str] = None

    # History
    history_db_path: str = ".openconch/history.db"

    # Search
    default_top_k: int = 10
    rerank_results: bool = True
