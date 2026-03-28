"""
Embedding generation for OpenConch.

Uses sentence-transformers for local embedding generation.
No API calls needed — runs on CPU, fast enough for memory operations.
"""

from typing import List, Optional
import numpy as np


class EmbeddingEngine:
    """
    Generates embeddings for memory text using sentence-transformers.

    Lazy-loads the model on first use to avoid startup overhead.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        """Lazy-load the sentence-transformer model."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)

    def embed(self, text: str) -> List[float]:
        """Embed a single text string."""
        self._load_model()
        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts efficiently."""
        self._load_model()
        embeddings = self._model.encode(texts, convert_to_numpy=True, batch_size=32)
        return embeddings.tolist()

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        self._load_model()
        return self._model.get_sentence_embedding_dimension()
