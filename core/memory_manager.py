"""
Semantic Memory Manager using LanceDB and embeddings.

Features:
- Stores messages with embedding vectors in a LanceDB collection for semantic search.
- Supports recent history in RAM for quick access and as a fallback.
- Pluggable embeddings (defaults to Ollama embeddings via langchain_ollama).
"""

from __future__ import annotations
import os
import datetime
from typing import List, Optional, Dict, Any
import asyncio

import logging

try:
    import lancedb  # type: ignore
except Exception:  # pragma: no cover - optional import for environments without lancedb
    lancedb = None  # type: ignore

try:
    from langchain_ollama import OllamaEmbeddings  # type: ignore
except Exception:  # pragma: no cover
    OllamaEmbeddings = None  # type: ignore

from core.config import settings


logger = logging.getLogger("nia.core.memory")


class MemoryManager:
    def __init__(
        self,
        persist: bool = True,
        max_items: int = 200,
        enabled: Optional[bool] = None,
        db_path: Optional[str] = None,
        collection: Optional[str] = None,
        embedding_model: Optional[str] = None,
        embeddings_client: Optional[Any] = None,
    ) -> None:
        """Initialize semantic memory.

        Parameters allow overriding config for testing.
        """
        self.persist = persist
        self.max_items = max_items
        self._history: List[dict] = []

        memory_cfg = settings.get("memory", {}) if isinstance(settings, dict) else {}
        self.enabled = enabled if enabled is not None else memory_cfg.get("enabled", True)
        self.db_path = db_path or memory_cfg.get("db_path", os.path.join("data", "memory"))
        self.collection = collection or memory_cfg.get("collection", "conversations")
        self.embedding_model = embedding_model or memory_cfg.get("embedding_model", "nomic-embed-text")
        self.enable_embeddings = bool(memory_cfg.get("enable_embeddings", True))
        self.max_recent_queries = int(memory_cfg.get("max_recent_queries", 5))
        self.min_similarity_score = float(memory_cfg.get("min_similarity_score", 0.7))

        self._db = None
        self._table = None
        self._embeddings = embeddings_client

        if self.enabled and self.persist:
            if lancedb is None:
                logger.warning("LanceDB not available; disabling persistent semantic memory.")
                self.enabled = False

        if self.enabled and self.persist:
            os.makedirs(self.db_path, exist_ok=True)
            try:
                self._db = lancedb.connect(self.db_path)
                try:
                    self._table = self._db.open_table(self.collection)
                except Exception:
                    # Table does not exist yet; will create on first insert
                    self._table = None
            except Exception as exc:
                logger.error("Failed to initialize LanceDB at '%s': %s", self.db_path, exc)
                self.enabled = False

        # Initialize embeddings if not injected
        if self._embeddings is None and self.enable_embeddings:
            if OllamaEmbeddings is None:
                logger.warning("OllamaEmbeddings not available; semantic ops will be disabled.")
            else:
                try:
                    self._embeddings = OllamaEmbeddings(model=self.embedding_model)
                except Exception as exc:  # pragma: no cover (depends on local ollama)
                    logger.error("Failed to initialize Ollama embeddings: %s", exc)
                    self._embeddings = None

    # Backward-compatible API used by interfaces
    def store(self, role: str, text: str) -> None:
        self.store_message(role, text)

    def session_history(self) -> List[dict]:
        return list(self._history)

    # New API
    def store_message(self, user: str, text: str) -> None:
        """Embed and store a message with metadata.

        Always appends to in-memory session history. If semantic memory is enabled,
        also stores to LanceDB with an embedding vector.
        """
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        entry = {"ts": timestamp, "user": user, "text": text}

        # Maintain recent in-memory buffer
        self._history.append(entry)
        if len(self._history) > self.max_items:
            self._history = self._history[-self.max_items:]

        # Persistent semantic store
        if not (self.enabled and self.persist and self._embeddings and self._db and self.enable_embeddings):
            return

        try:
            vector = self._embeddings.embed_query(text)
        except Exception as exc:  # pragma: no cover
            logger.warning("Embedding failed; message stored without vector: %s", exc)
            vector = None

        record: Dict[str, Any] = {
            "ts": timestamp,
            "user": user,
            "text": text,
            "vector": vector,
        }

        try:
            if self._table is None:
                # Create table on first insert using this record as schema
                self._table = self._db.create_table(self.collection, data=[record])
            else:
                self._table.add([record])
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to write to LanceDB: %s", exc)

    def get_similar_messages(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Return top K semantically similar messages for a query.

        Falls back to recent messages if semantic memory is unavailable.
        """
        if not (self.enabled and self.persist and self._embeddings and self._table and self.enable_embeddings):
            # Fallback: return recent messages that contain the query substring
            lowered = query.lower()
            candidates = [
                m for m in reversed(self._history)
                if lowered in m.get("text", "").lower()
            ]
            return candidates[:top_k]

        try:
            qvec = self._embeddings.embed_query(query)
            results = (
                self._table.search(qvec)  # type: ignore[attr-defined]
                .metric("cosine")
                .limit(top_k)
                .to_list()
            )
            # Normalize result shape to list of dicts with ts,user,text and optional score
            normalized: List[Dict[str, Any]] = []
            for item in results:
                # Some clients include distance/score; preserve if present
                norm = {k: item.get(k) for k in ("ts", "user", "text")}
                if "score" in item:
                    norm["score"] = item["score"]
                normalized.append(norm)  # type: ignore[arg-type]
            return normalized
        except Exception as exc:  # pragma: no cover
            logger.error("Similarity search failed: %s", exc)
            return []

    def get_recent_messages(self, n: int = 5) -> List[Dict[str, Any]]:
        """Return the most recent n messages from persistent store if available, else RAM."""
        if self.enabled and self.persist and self._table is not None:
            try:
                # Fetch all then sort by ts to avoid dependency on SQL syntax
                rows = self._table.to_list()
                rows.sort(key=lambda r: r.get("ts", ""), reverse=True)
                return [
                    {k: row.get(k) for k in ("ts", "user", "text")}
                    for row in rows[:n]
                ]
            except Exception as exc:  # pragma: no cover
                logger.warning("Failed to read recent messages from LanceDB: %s", exc)
        return list(self._history[-n:])

    def clear_memory(self) -> None:
        """Wipe the collection/storage."""
        self._history.clear()
        if self.enabled and self.persist and self._db is not None:
            try:
                if self._table is not None:
                    # Drop and recreate empty
                    self._db.drop_table(self.collection)
                    self._table = None
            except Exception as exc:  # pragma: no cover
                logger.warning("Failed to drop LanceDB table: %s", exc)

    # New async semantic query APIs
    async def query_memory(self, topic: Optional[str] = None, recent_n: int = 5, min_score: Optional[float] = None) -> List[Dict[str, Any]]:
        """Asynchronously query semantic memory by topic or return recent messages.

        - topic: text to embed and search; if None, returns recent_n most recent messages
        - recent_n: number of items to return
        - min_score: minimum cosine similarity score to include (defaults to config)
        """
        threshold = self.min_similarity_score if min_score is None else float(min_score)

        if not topic:
            # Return recent from persistent if possible, else RAM
            return self.get_recent_messages(n=recent_n)

        # Offload embedding + search to a thread to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._blocking_query, topic, recent_n, threshold)

    def _blocking_query(self, topic: str, recent_n: int, threshold: float) -> List[Dict[str, Any]]:
        # If semantic stack unavailable, fallback to substring search in RAM
        if not (self.enabled and self.persist and self._embeddings and self._table and self.enable_embeddings):
            lowered = topic.lower()
            hits = [m for m in reversed(self._history) if lowered in m.get("text", "").lower()]
            return hits[:recent_n]

        try:
            qvec = self._embeddings.embed_query(topic)
            results = (
                self._table.search(qvec)  # type: ignore[attr-defined]
                .metric("cosine")
                .limit(recent_n)
                .to_list()
            )
            filtered: List[Dict[str, Any]] = []
            for item in results:
                score = item.get("score", 1.0)
                if score is None or score >= threshold:
                    filtered.append({k: item.get(k) for k in ("ts", "user", "text")} | ({"score": score} if score is not None else {}))
            return filtered
        except Exception as exc:  # pragma: no cover
            logger.warning("Semantic query failed: %s", exc)
            return []

    async def get_relevant_history(self, text: str, n: int = 5) -> List[Dict[str, Any]]:
        """Convenience wrapper to fetch top-N relevant messages for a given text."""
        return await self.query_memory(topic=text, recent_n=n)
