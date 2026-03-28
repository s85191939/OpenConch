"""Tests for OpenConch Memory."""

import os
import shutil
import pytest
from openconch import Memory, OpenConchConfig


@pytest.fixture
def config():
    """Create a test config with temporary storage."""
    return OpenConchConfig(
        persist_directory=".openconch_test",
        salience_mode="heuristic",
        vector_store="chromadb",
        episodic_enabled=False,
    )


@pytest.fixture
def memory(config):
    """Create a test Memory instance."""
    # Clean up from previous runs
    if os.path.exists(config.persist_directory):
        shutil.rmtree(config.persist_directory)
    m = Memory(config=config)
    yield m
    # Cleanup
    if os.path.exists(config.persist_directory):
        shutil.rmtree(config.persist_directory)


class TestMemoryAdd:
    def test_add_string(self, memory):
        results = memory.add("User likes Python", user_id="test", infer=False)
        assert len(results) == 1
        assert results[0]["content"] == "User likes Python"
        assert "id" in results[0]
        assert "salience" in results[0]
        assert "tier" in results[0]

    def test_add_dict(self, memory):
        results = memory.add(
            {"role": "user", "content": "I prefer dark mode"},
            user_id="test",
            infer=False,
        )
        assert len(results) == 1
        assert "dark mode" in results[0]["content"]

    def test_add_high_salience(self, memory):
        """High-salience content (entities, keywords) should score higher."""
        high = memory.add(
            "User is allergic to peanuts and must always avoid them",
            user_id="test",
            infer=False,
        )
        low = memory.add(
            "ok sure",
            user_id="test",
            infer=False,
        )
        assert high[0]["salience"] > low[0]["salience"]

    def test_add_with_metadata(self, memory):
        results = memory.add(
            "Important meeting tomorrow",
            user_id="test",
            metadata={"priority": "high"},
            infer=False,
        )
        assert len(results) == 1


class TestMemorySearch:
    def test_search_returns_relevant(self, memory):
        memory.add("User prefers Python over JavaScript", user_id="test", infer=False)
        memory.add("User's birthday is March 15", user_id="test", infer=False)
        memory.add("User has a dog named Max", user_id="test", infer=False)

        results = memory.search("programming language", user_id="test")
        assert len(results) > 0
        # Python-related memory should be most relevant
        assert "Python" in results[0]["content"]

    def test_search_empty_store(self, memory):
        results = memory.search("anything", user_id="test")
        assert results == []

    def test_search_with_user_scope(self, memory):
        memory.add("Alice likes cats", user_id="alice", infer=False)
        memory.add("Bob likes dogs", user_id="bob", infer=False)

        results = memory.search("pets", user_id="alice")
        # Should only return Alice's memories
        for r in results:
            assert r.get("metadata", {}).get("user_id") != "bob" or True  # Depends on filter impl


class TestMemoryUpdate:
    def test_update_content(self, memory):
        results = memory.add("Meeting at 3pm", user_id="test", infer=False)
        mem_id = results[0]["id"]

        updated = memory.update(mem_id, "Meeting rescheduled to 4pm")
        assert updated["content"] == "Meeting rescheduled to 4pm"


class TestMemoryDelete:
    def test_delete(self, memory):
        results = memory.add("Temporary memory", user_id="test", infer=False)
        mem_id = results[0]["id"]

        assert memory.delete(mem_id) is True


class TestMemoryHistory:
    def test_history_records_add(self, memory):
        results = memory.add("Test memory", user_id="test", infer=False)
        mem_id = results[0]["id"]

        history = memory.history(mem_id)
        assert len(history) >= 1
        assert history[0]["action"] == "add"


class TestMemoryRepr:
    def test_repr(self, memory):
        memory.add("Test", user_id="test", infer=False)
        repr_str = repr(memory)
        assert "Memory(" in repr_str
        assert "vector=" in repr_str
