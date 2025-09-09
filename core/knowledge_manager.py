"""
KnowledgeManager — Multi-source retrieval over LanceDB with optional Haystack.

Design goals:
- Store long-term knowledge documents with embeddings in LanceDB.
- Provide a simple API for add/query/clear.
- Prefer Haystack components if available; gracefully fall back to direct LanceDB ops.
- Share embedding client with MemoryManager style (default Ollama embeddings), injectable for tests.
"""

from __future__ import annotations
import os
from typing import List, Dict, Any, Optional
import logging

try:
    import lancedb  # type: ignore
except Exception:  # pragma: no cover
    lancedb = None  # type: ignore

try:
    from langchain_ollama import OllamaEmbeddings  # type: ignore
except Exception:  # pragma: no cover
    OllamaEmbeddings = None  # type: ignore

try:
    # Optional Haystack integration
    from haystack import Document  # type: ignore
except Exception:  # pragma: no cover
    Document = None  # type: ignore

from core.config import settings


logger = logging.getLogger("nia.core.knowledge")


class KnowledgeManager:
    def __init__(
        self,
        index_path: Optional[str] = None,
        collection: str = "documents",
        embedding_model: Optional[str] = None,
        embeddings_client: Optional[Any] = None,
        enabled: Optional[bool] = None,
    ) -> None:
        cfg = settings.get("knowledge", {}) if isinstance(settings, dict) else {}
        self.enabled = enabled if enabled is not None else bool(cfg.get("enabled", True))
        self.index_path = index_path or cfg.get("index_path", os.path.join("data", "knowledge"))
        self.collection = collection
        self.top_k_default = int(cfg.get("top_k", 5))
        self.embedding_model = embedding_model or settings.get("memory", {}).get("embedding_model", "nomic-embed-text")
        self._embeddings = embeddings_client
        self._db = None
        self._table = None

        # In-memory fallback store (list of dict records)
        self._inmem_store: List[Dict[str, Any]] = []

        if not self.enabled:
            return

        if lancedb is None:
            logger.warning("LanceDB not available; KnowledgeManager will use in-memory store.")
            # proceed with in-memory fallback
        else:
            os.makedirs(self.index_path, exist_ok=True)
            try:
                self._db = lancedb.connect(self.index_path)
                try:
                    self._table = self._db.open_table(self.collection)
                except Exception:
                    self._table = None
            except Exception as exc:  # pragma: no cover
                logger.error("Failed to initialize LanceDB for KnowledgeManager: %s", exc)
                # fallback to in-memory
                self._db = None
                self._table = None

        if self._embeddings is None and OllamaEmbeddings is not None:
            try:
                self._embeddings = OllamaEmbeddings(model=self.embedding_model)
            except Exception as exc:  # pragma: no cover
                logger.error("Failed to initialize Ollama embeddings for KnowledgeManager: %s", exc)
                self._embeddings = None

    def add_source(self, name: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        if not self.enabled:
            return
        metadata = metadata or {}
        # Build record
        vector = None
        if self._embeddings is not None:
            try:
                vector = self._embeddings.embed_query(text)
            except Exception as exc:  # pragma: no cover
                logger.warning("Embedding failed for knowledge '%s': %s", name, exc)

        record: Dict[str, Any] = {
            "name": name,
            "text": text,
            "vector": vector,
            "source": metadata.get("source", name),
            "meta": metadata,
        }

        if self._db is not None:
            try:
                if self._table is None:
                    self._table = self._db.create_table(self.collection, data=[record])
                else:
                    self._table.add([record])
            except Exception as exc:  # pragma: no cover
                logger.error("Failed adding knowledge record: %s", exc)
        else:
            # In-memory fallback
            self._inmem_store.append(record)

    def query(self, query_text: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        if not self.enabled or self._embeddings is None:
            return []
        k = int(top_k or self.top_k_default)
        try:
            qvec = self._embeddings.embed_query(query_text)
            if self._table is not None:
                results = (
                    self._table.search(qvec)  # type: ignore[attr-defined]
                    .metric("cosine")
                    .limit(k)
                    .to_list()
                )
                normalized: List[Dict[str, Any]] = []
                for r in results:
                    normalized.append({
                        "name": r.get("name"),
                        "text": r.get("text"),
                        "source": r.get("source"),
                        "meta": r.get("meta", {}),
                        **({"score": r.get("score")} if "score" in r else {}),
                    })
                return normalized
            else:
                # In-memory cosine similarity search
                def cosine(a: List[float], b: List[float]) -> float:
                    if not a or not b or len(a) != len(b):
                        return 0.0
                    dot = sum(x*y for x, y in zip(a, b))
                    na = sum(x*x for x in a) ** 0.5
                    nb = sum(y*y for y in b) ** 0.5
                    if na == 0 or nb == 0:
                        return 0.0
                    return dot / (na * nb)

                scored = []
                for r in self._inmem_store:
                    vec = r.get("vector")
                    score = cosine(qvec, vec) if vec else 0.0
                    scored.append((score, r))
                scored.sort(key=lambda t: t[0], reverse=True)
                top = [r for _, r in scored[:k]]
                return [{
                    "name": r.get("name"),
                    "text": r.get("text"),
                    "source": r.get("source"),
                    "meta": r.get("meta", {}),
                    "score": s
                } for s, r in scored[:k]]
        except Exception as exc:  # pragma: no cover
            logger.error("Knowledge query failed: %s", exc)
            return []

    def clear_index(self) -> None:
        if not self.enabled:
            return
        if self._db is not None:
            try:
                self._db.drop_table(self.collection)
                self._table = None
            except Exception as exc:  # pragma: no cover
                logger.warning("Failed clearing knowledge index: %s", exc)
        # Clear in-memory store too
        self._inmem_store.clear()

    def query_with_memory(self, query_text: str, memory_manager) -> Dict[str, List[Dict[str, Any]]]:
        """Combine knowledge retrieval with semantic memory similar messages."""
        knowledge_docs = self.query(query_text)
        memory_snippets = []
        try:
            memory_snippets = memory_manager.get_similar_messages(query_text, top_k=5) if memory_manager else []
        except Exception:
            memory_snippets = []
        return {"knowledge": knowledge_docs, "memory": memory_snippets}


