"""
OpenConch Memory — the public API.

Drop-in compatible with mem0's Memory class. Same method signatures,
better internals: Mamba-powered salience scoring, episodic memory
with temporal understanding, and learned retrieval.

Usage:
    from openconch import Memory

    m = Memory()
    m.add("I prefer dark mode in all applications", user_id="alice")
    m.add("My meeting with Bob is at 3pm tomorrow", user_id="alice")

    results = m.search("What are Alice's preferences?", user_id="alice")
    for r in results:
        print(r["content"], r["score"])
"""

from typing import List, Dict, Optional, Union
from openconch.config import OpenConchConfig
from openconch.router import MemoryRouter
from openconch.llm import LLMEngine


class Memory:
    """
    OpenConch Memory — episodic memory for AI agents.

    Compatible with mem0's API surface. Internally routes through:
    - Salience scorer (heuristic or Mamba-based)
    - Episodic memory store (fixed-size, temporally-aware)
    - Vector store (ChromaDB/Qdrant for broad semantic search)
    - LLM (Claude for fact extraction)
    """

    def __init__(self, config: Optional[OpenConchConfig] = None):
        self.config = config or OpenConchConfig()
        self.router = MemoryRouter(self.config)
        self._llm = None

    @property
    def llm(self) -> LLMEngine:
        """Lazy-load LLM engine."""
        if self._llm is None:
            self._llm = LLMEngine(
                model=self.config.llm_model,
                api_key=self.config.llm_api_key,
            )
        return self._llm

    def add(
        self,
        messages: Union[str, List[Dict], Dict],
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[dict] = None,
        infer: bool = True,
    ) -> List[Dict]:
        """
        Add memories from a message or conversation.

        Args:
            messages: String, single message dict, or list of message dicts.
                String: stored directly as a memory
                Dict: {"role": "user", "content": "..."} format
                List: conversation to extract facts from
            user_id: Scope to a specific user
            agent_id: Scope to a specific agent
            session_id: Scope to a specific session
            metadata: Additional metadata to store
            infer: If True, use LLM to extract facts from conversations.
                   If False, store the raw text directly.

        Returns:
            List of dicts with id, content, salience, tier for each memory added.
        """
        # Normalize input to list of text strings
        texts = self._normalize_messages(messages, infer)

        results = []
        for text in texts:
            result = self.router.add(
                content=text,
                user_id=user_id,
                agent_id=agent_id,
                session_id=session_id,
                metadata=metadata,
            )
            results.append(result)

        return results

    def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        top_k: Optional[int] = None,
        filters: Optional[dict] = None,
    ) -> List[Dict]:
        """
        Search for relevant memories.

        Uses both semantic similarity (vector store) and temporal
        relevance (episodic store with Mamba) to find the most
        useful memories.

        Args:
            query: Search query text
            user_id: Filter to a specific user
            agent_id: Filter to a specific agent
            session_id: Filter to a specific session
            top_k: Number of results (default from config)
            filters: Additional metadata filters

        Returns:
            List of dicts with id, content, score, metadata.
            Sorted by relevance (highest first).
        """
        return self.router.search(
            query=query,
            top_k=top_k or self.config.default_top_k,
            user_id=user_id,
            agent_id=agent_id,
            session_id=session_id,
            filters=filters,
        )

    def update(self, memory_id: str, content: str) -> Dict:
        """
        Update a memory's content.

        Re-scores salience and may promote/demote between stores.

        Args:
            memory_id: ID of memory to update
            content: New content

        Returns:
            Dict with updated memory info
        """
        return self.router.update(memory_id, content)

    def delete(self, memory_id: str) -> bool:
        """
        Delete a memory from all stores.

        Args:
            memory_id: ID of memory to delete

        Returns:
            True if deleted, False if not found
        """
        return self.router.delete(memory_id)

    def get(self, memory_id: str) -> Optional[Dict]:
        """
        Get a specific memory by ID.

        Args:
            memory_id: Memory ID

        Returns:
            Dict with memory content and metadata, or None
        """
        return self.router.get(memory_id)

    def get_all(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get all memories, optionally filtered by scope.

        Args:
            user_id: Filter to a specific user
            agent_id: Filter to a specific agent
            session_id: Filter to a specific session

        Returns:
            List of all matching memories
        """
        return self.router.get_all(user_id, agent_id, session_id)

    def history(self, memory_id: str) -> List[Dict]:
        """
        Get the change history for a specific memory.

        Every add, update, delete is recorded with timestamps.

        Args:
            memory_id: Memory ID to get history for

        Returns:
            List of history entries (newest first)
        """
        return self.router.history.get_history(memory_id)

    def _normalize_messages(self, messages, infer: bool) -> List[str]:
        """
        Normalize input to a list of text strings to store.

        If infer=True and input is a conversation, uses LLM to
        extract facts. Otherwise, stores raw text.
        """
        # String input
        if isinstance(messages, str):
            if infer:
                try:
                    facts = self.llm.extract_facts(messages)
                    return facts if facts else [messages]
                except Exception:
                    return [messages]
            return [messages]

        # Single message dict
        if isinstance(messages, dict):
            content = messages.get("content", str(messages))
            return self._normalize_messages(content, infer)

        # List of message dicts (conversation)
        if isinstance(messages, list):
            # Build conversation string
            conversation = ""
            for msg in messages:
                if isinstance(msg, dict):
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    conversation += f"{role}: {content}\n"
                else:
                    conversation += f"{msg}\n"

            if infer:
                try:
                    facts = self.llm.extract_facts(conversation)
                    return facts if facts else [conversation.strip()]
                except Exception:
                    return [conversation.strip()]
            return [conversation.strip()]

        return [str(messages)]

    def __repr__(self) -> str:
        vector_count = self.router.vector_store.count()
        episodic_info = ""
        if self.router.episodic_store:
            es = self.router.episodic_store
            episodic_info = f", episodic={es.size}/{es.capacity}"
        return f"Memory(vector={vector_count}{episodic_info}, scorer={self.config.salience_mode})"
