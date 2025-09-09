import os
import shutil
import tempfile

import pytest

from core.memory_manager import MemoryManager
from core.autonomy_agent import AutonomyAgent
import asyncio


class FakeEmbeddings:
    """Deterministic embedding for tests: map text to vector of char codes sum, len."""

    def embed_query(self, text: str):
        total = sum(ord(c) for c in text)
        length = len(text)
        # Small fixed-size vector to satisfy LanceDB requirements
        return [float(total), float(length), float(total % 97), float(length % 13)]


@pytest.fixture()
def tmp_lancedb_dir():
    path = tempfile.mkdtemp(prefix="nia_mem_")
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_store_and_recent_messages(tmp_lancedb_dir):
    mm = MemoryManager(
        persist=True,
        enabled=True,
        db_path=tmp_lancedb_dir,
        collection="tests",
        embeddings_client=FakeEmbeddings(),
    )

    mm.clear_memory()
    mm.store_message("user", "hello world")
    mm.store_message("nia", "hi there")

    recent = mm.get_recent_messages(2)
    assert len(recent) == 2
    assert recent[0]["text"] in {"hello world", "hi there"}


def test_similarity_retrieval(tmp_lancedb_dir):
    mm = MemoryManager(
        persist=True,
        enabled=True,
        db_path=tmp_lancedb_dir,
        collection="tests",
        embeddings_client=FakeEmbeddings(),
    )

    mm.clear_memory()
    mm.store_message("user", "I like apples and bananas")
    mm.store_message("user", "Apples are my favorite fruit")
    mm.store_message("user", "Let's talk about cars and engines")

    results = mm.get_similar_messages("apples", top_k=2)
    assert len(results) == 2
    # Should contain apple-related entries
    texts = {r["text"] for r in results}
    assert any("apple" in t.lower() for t in texts)


def test_clear_memory(tmp_lancedb_dir):
    mm = MemoryManager(
        persist=True,
        enabled=True,
        db_path=tmp_lancedb_dir,
        collection="tests",
        embeddings_client=FakeEmbeddings(),
    )
    mm.store_message("user", "something")
    assert len(mm.get_recent_messages(5)) >= 1
    mm.clear_memory()
    # After clearing, there should be no persistent rows
    recent = mm.get_recent_messages(5)
    # Either empty (if persistent available) or only in-memory cleared
    assert len(recent) == 0


@pytest.mark.asyncio
async def test_async_semantic_query(tmp_lancedb_dir):
    mm = MemoryManager(
        persist=True,
        enabled=True,
        db_path=tmp_lancedb_dir,
        collection="tests",
        embeddings_client=FakeEmbeddings(),
    )
    mm.clear_memory()
    mm.store_message("user", "Discuss project roadmap and deadlines")
    mm.store_message("nia", "We can plan milestones for the project")
    mm.store_message("user", "Let's talk about weekend plans")

    hits = await mm.query_memory(topic="project", recent_n=2, min_score=0.0)
    assert len(hits) == 2
    assert any("project" in h["text"].lower() for h in hits)


@pytest.mark.asyncio
async def test_autonomy_uses_async_memory(monkeypatch, tmp_lancedb_dir):
    loop = asyncio.get_event_loop()
    mm = MemoryManager(
        persist=True,
        enabled=True,
        db_path=tmp_lancedb_dir,
        collection="tests",
        embeddings_client=FakeEmbeddings(),
    )
    mm.clear_memory()
    mm.store_message("user", "I need help deciding about my work project")
    mm.store_message("nia", "Consider scope, timeline, and resources")

    agent = AutonomyAgent(loop, memory=mm)
    agent.enabled = True
    agent.confidence_threshold = 0.1
    agent.update_user_input("What should I do for the project?")
    suggestion = agent._generate_context_aware_suggestion()
    assert suggestion is not None
    assert suggestion.metadata and "memory_context" in suggestion.metadata

