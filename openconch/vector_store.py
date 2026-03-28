"""
Vector Store — ChromaDB or Qdrant backend for semantic search.

This is the traditional embedding-based memory store. It complements
the episodic store: vectors give you broad semantic recall ("find
anything related to X"), while episodic gives you precise temporal
retrieval ("what exactly did the user say about X last Tuesday?").
"""

import os
from typing import List, Dict, Optional
from openconch.utils import generate_id, now_timestamp


class VectorStore:
    """
    Vector embedding store with ChromaDB (default) or Qdrant backend.

    Provides standard CRUD + similarity search over memory embeddings.
    """

    def __init__(
        self,
        backend: str = "chromadb",
        collection_name: str = "openconch_memories",
        persist_directory: str = ".openconch",
        qdrant_url: Optional[str] = None,
    ):
        self.backend = backend
        self.collection_name = collection_name
        self.persist_directory = persist_directory

        if backend == "chromadb":
            self._init_chromadb()
        elif backend == "qdrant":
            self._init_qdrant(qdrant_url)
        else:
            raise ValueError(f"Unknown backend: {backend}. Use 'chromadb' or 'qdrant'.")

    def _init_chromadb(self):
        """Initialize ChromaDB client and collection."""
        import chromadb
        os.makedirs(self.persist_directory, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def _init_qdrant(self, url: Optional[str]):
        """Initialize Qdrant client and collection."""
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams

        if url:
            self.client = QdrantClient(url=url)
        else:
            self.client = QdrantClient(path=os.path.join(self.persist_directory, "qdrant"))

        # Create collection if it doesn't exist
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in collections:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )

    def add(
        self,
        memory_id: str,
        content: str,
        embedding: List[float],
        metadata: Optional[dict] = None,
    ) -> str:
        """Add a memory to the vector store."""
        meta = metadata or {}
        meta["content"] = content
        meta["created_at"] = now_timestamp()

        if self.backend == "chromadb":
            self.collection.add(
                ids=[memory_id],
                embeddings=[embedding],
                metadatas=[meta],
                documents=[content],
            )
        elif self.backend == "qdrant":
            from qdrant_client.models import PointStruct
            self.client.upsert(
                collection_name=self.collection_name,
                points=[PointStruct(
                    id=memory_id,
                    vector=embedding,
                    payload=meta,
                )],
            )

        return memory_id

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[dict] = None,
    ) -> List[Dict]:
        """
        Search for similar memories.

        Returns list of dicts with id, content, score, metadata.
        """
        if self.backend == "chromadb":
            where = filters if filters else None
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where,
            )

            memories = []
            if results["ids"] and results["ids"][0]:
                for i, mem_id in enumerate(results["ids"][0]):
                    meta = results["metadatas"][0][i] if results["metadatas"] else {}
                    content = results["documents"][0][i] if results["documents"] else meta.get("content", "")
                    distance = results["distances"][0][i] if results["distances"] else 0
                    # ChromaDB returns distance, convert to similarity
                    similarity = 1.0 - distance

                    memories.append({
                        "id": mem_id,
                        "content": content,
                        "score": similarity,
                        "metadata": {k: v for k, v in meta.items() if k not in ("content",)},
                    })
            return memories

        elif self.backend == "qdrant":
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
            )
            return [
                {
                    "id": str(r.id),
                    "content": r.payload.get("content", ""),
                    "score": r.score,
                    "metadata": {k: v for k, v in r.payload.items() if k != "content"},
                }
                for r in results
            ]

    def update(self, memory_id: str, content: str, embedding: List[float], metadata: Optional[dict] = None):
        """Update an existing memory."""
        meta = metadata or {}
        meta["content"] = content
        meta["updated_at"] = now_timestamp()

        if self.backend == "chromadb":
            self.collection.update(
                ids=[memory_id],
                embeddings=[embedding],
                metadatas=[meta],
                documents=[content],
            )
        elif self.backend == "qdrant":
            from qdrant_client.models import PointStruct
            self.client.upsert(
                collection_name=self.collection_name,
                points=[PointStruct(id=memory_id, vector=embedding, payload=meta)],
            )

    def delete(self, memory_id: str):
        """Delete a memory."""
        if self.backend == "chromadb":
            self.collection.delete(ids=[memory_id])
        elif self.backend == "qdrant":
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[memory_id],
            )

    def get(self, memory_id: str) -> Optional[Dict]:
        """Get a specific memory by ID."""
        if self.backend == "chromadb":
            result = self.collection.get(ids=[memory_id])
            if result["ids"]:
                meta = result["metadatas"][0] if result["metadatas"] else {}
                return {
                    "id": memory_id,
                    "content": result["documents"][0] if result["documents"] else meta.get("content", ""),
                    "metadata": meta,
                }
        elif self.backend == "qdrant":
            results = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[memory_id],
            )
            if results:
                r = results[0]
                return {
                    "id": str(r.id),
                    "content": r.payload.get("content", ""),
                    "metadata": r.payload,
                }
        return None

    def count(self) -> int:
        """Get total number of memories."""
        if self.backend == "chromadb":
            return self.collection.count()
        elif self.backend == "qdrant":
            info = self.client.get_collection(self.collection_name)
            return info.points_count
