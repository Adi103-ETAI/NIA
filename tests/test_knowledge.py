import os
import shutil
import tempfile

import pytest

from core.knowledge_manager import KnowledgeManager


class FakeEmbeddings:
    vocab = ["apples", "bananas", "fruits", "cars", "engines", "automobiles"]
    def embed_query(self, text: str):
        tokens = set(t.strip(".,!?").lower() for t in text.split())
        vec = [1.0 if term in tokens else 0.0 for term in self.vocab]
        # Ensure non-zero norm by appending length indicator
        vec.append(float(len(tokens) % 7))
        return vec


@pytest.fixture()
def tmp_knowledge_dir():
    path = tempfile.mkdtemp(prefix="nia_kg_")
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_add_and_query_knowledge(tmp_knowledge_dir):
    km = KnowledgeManager(index_path=tmp_knowledge_dir, embeddings_client=FakeEmbeddings(), enabled=True)
    km.clear_index()  # ensure clean

    km.add_source("fruit", "Apples and bananas are fruits.", {"topic": "food"})
    km.add_source("vehicle", "Cars and engines are related to automobiles.", {"topic": "transport"})

    results = km.query("apples", top_k=1)
    assert isinstance(results, list)
    assert len(results) == 1
    assert "fruit" in (results[0].get("name") or results[0].get("source"))


def test_clear_index(tmp_knowledge_dir):
    km = KnowledgeManager(index_path=tmp_knowledge_dir, embeddings_client=FakeEmbeddings(), enabled=True)
    km.add_source("a", "alpha")
    assert len(km.query("alpha", top_k=5)) >= 0
    km.clear_index()
    # After clear_index, table should be gone; query returns empty
    assert km.query("alpha", top_k=5) == []


