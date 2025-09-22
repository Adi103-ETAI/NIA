"""
Enhanced Memory Manager for NIA with database integration.

Combines vector-based semantic search with structured database storage for comprehensive memory management.
"""

from __future__ import annotations
import os
import datetime
import hashlib
from typing import List, Optional, Dict, Any, Union
import asyncio
import logging

try:
    import lancedb  # type: ignore
except Exception:
    lancedb = None  # type: ignore

try:
    from langchain_ollama import OllamaEmbeddings  # type: ignore
except Exception:
    OllamaEmbeddings = None  # type: ignore

from core.config import settings
from core.database.manager import get_db_manager, DatabaseManager

logger = logging.getLogger("nia.core.memory_enhanced")


class EnhancedMemoryManager:
    """Enhanced memory manager with both vector and structured storage."""
    
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
        """Initialize enhanced memory with both vector and structured storage."""
        self.persist = persist
        self.max_items = max_items
        self._history: List[dict] = []
        
        # Configuration
        memory_cfg = settings.get("memory", {}) if isinstance(settings, dict) else {}
        vector_cfg = memory_cfg.get("vector_db", {})
        structured_cfg = memory_cfg.get("structured_db", {})
        
        self.enabled = enabled if enabled is not None else memory_cfg.get("enabled", True)
        self.structured_enabled = structured_cfg.get("enabled", True)
        
        # Vector storage configuration
        self.db_path = db_path or vector_cfg.get("path", os.path.join("data", "memory"))
        self.collection = collection or vector_cfg.get("collection", "conversations")
        self.embedding_model = embedding_model or vector_cfg.get("embedding_model", "nomic-embed-text")
        self.enable_embeddings = bool(vector_cfg.get("enable_embeddings", True))
        self.max_recent_queries = int(vector_cfg.get("max_recent_queries", 5))
        self.min_similarity_score = float(vector_cfg.get("min_similarity_score", 0.7))
        
        # Initialize database manager for structured storage
        self.db_manager: Optional[DatabaseManager] = None
        if self.structured_enabled:
            try:
                self.db_manager = get_db_manager()
                logger.info("Structured database manager initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize structured database: {e}")
                self.structured_enabled = False
        
        # Vector storage initialization
        self._db = None
        self._table = None
        self._embeddings = embeddings_client
        
        if self.enabled and self.persist:
            self._initialize_vector_storage()
        
        # Initialize embeddings
        if self._embeddings is None and self.enable_embeddings:
            self._initialize_embeddings()
        
        logger.info("Enhanced memory manager initialized")
    
    def _initialize_vector_storage(self):
        """Initialize vector storage (LanceDB)."""
        if lancedb is None:
            logger.warning("LanceDB not available; disabling vector storage.")
            return
        
        try:
            os.makedirs(self.db_path, exist_ok=True)
            self._db = lancedb.connect(self.db_path)
            try:
                self._table = self._db.open_table(self.collection)
            except Exception:
                # Table does not exist yet; will create on first insert
                self._table = None
            logger.info("Vector storage initialized")
        except Exception as exc:
            logger.error("Failed to initialize LanceDB at '%s': %s", self.db_path, exc)
            self.enabled = False
    
    def _initialize_embeddings(self):
        """Initialize embedding client."""
        if OllamaEmbeddings is None:
            logger.warning("OllamaEmbeddings not available; semantic ops will be disabled.")
            return
        
        try:
            self._embeddings = OllamaEmbeddings(model=self.embedding_model)
            logger.info(f"Embeddings initialized with model: {self.embedding_model}")
        except Exception as exc:
            logger.error("Failed to initialize Ollama embeddings: %s", exc)
            self._embeddings = None
    
    # Enhanced API combining both storage methods
    async def store_message(
        self,
        user: str,
        text: str,
        session_id: str = "default",
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Store a message in both vector and structured storage.
        
        Args:
            user: Role/user identifier (user, assistant, system)
            text: Message content
            session_id: Session identifier for grouping conversations
            user_id: User identifier for multi-user support
            metadata: Additional metadata (response_time, model_used, etc.)
        
        Returns:
            Message ID if successfully stored in structured DB, None otherwise
        """
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        entry = {
            "ts": timestamp,
            "user": user,
            "text": text,
            "session_id": session_id,
            "user_id": user_id
        }
        
        # Add to in-memory history
        self._history.append(entry)
        if len(self._history) > self.max_items:
            self._history = self._history[-self.max_items:]
        
        # Store in structured database
        conversation_id = None
        if self.structured_enabled and self.db_manager:
            try:
                conversation_id = await self.db_manager.store_conversation(
                    role=user,
                    content=text,
                    session_id=session_id,
                    user_id=user_id,
                    metadata=metadata
                )
                logger.debug(f"Stored conversation in structured DB: {conversation_id}")
            except Exception as e:
                logger.error(f"Failed to store in structured DB: {e}")
        
        # Store in vector storage
        if self.enabled and self.persist and self._embeddings and self._db and self.enable_embeddings:
            await self._store_in_vector_db(entry)
        
        return conversation_id
    
    async def _store_in_vector_db(self, entry: Dict[str, Any]):
        """Store entry in vector database."""
        try:
            # Generate embedding
            text = entry["text"]
            vector = None
            if self._embeddings:
                vector = await asyncio.get_event_loop().run_in_executor(
                    None, self._embeddings.embed_query, text
                )
            
            # Prepare record
            record: Dict[str, Any] = {
                "ts": entry["ts"],
                "user": entry["user"],
                "text": text,
                "session_id": entry.get("session_id", "default"),
                "user_id": entry.get("user_id"),
                "vector": vector,
                "content_hash": hashlib.md5(text.encode()).hexdigest()
            }
            
            # Store in LanceDB
            def _store_record():
                if self._table is None:
                    self._table = self._db.create_table(self.collection, data=[record])
                else:
                    self._table.add([record])
            
            await asyncio.get_event_loop().run_in_executor(None, _store_record)
            logger.debug("Stored in vector database")
            
        except Exception as exc:
            logger.error("Failed to write to vector DB: %s", exc)
    
    async def query_memory(
        self,
        topic: Optional[str] = None,
        recent_n: int = 5,
        min_score: Optional[float] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        include_structured: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Query memory from both vector and structured storage.
        
        Args:
            topic: Text to search for semantically
            recent_n: Number of results to return
            min_score: Minimum similarity score
            session_id: Filter by session ID
            user_id: Filter by user ID
            include_structured: Whether to include structured DB results
        
        Returns:
            Combined results from both storage systems
        """
        results = []
        
        # Query structured database first for recent conversations
        if include_structured and self.structured_enabled and self.db_manager:
            try:
                structured_results = await self.db_manager.get_conversation_history(
                    session_id=session_id or "default",
                    limit=recent_n,
                    user_id=user_id
                )
                
                # Convert to consistent format
                for result in structured_results:
                    results.append({
                        "ts": result["created_at"].isoformat() + "Z",
                        "user": result["role"],
                        "text": result["content"],
                        "source": "structured_db",
                        "response_time": result.get("response_time"),
                        "model_used": result.get("model_used"),
                        "provider_used": result.get("provider_used")
                    })
                
                logger.debug(f"Found {len(structured_results)} results from structured DB")
            except Exception as e:
                logger.error(f"Error querying structured DB: {e}")
        
        # If no topic provided, return recent results
        if not topic:
            # Add recent from memory if structured DB didn't provide enough
            if len(results) < recent_n:
                memory_results = self._get_recent_from_memory(recent_n - len(results))
                results.extend(memory_results)
            return results[:recent_n]
        
        # Query vector database for semantic search
        if self.enabled and self.persist and self._embeddings and self._table and self.enable_embeddings:
            try:
                vector_results = await self._query_vector_db(topic, recent_n, min_score, session_id, user_id)
                
                # Merge results, avoiding duplicates based on content hash
                seen_hashes = set()
                for result in results:
                    content_hash = hashlib.md5(result["text"].encode()).hexdigest()
                    seen_hashes.add(content_hash)
                
                for vector_result in vector_results:
                    content_hash = hashlib.md5(vector_result["text"].encode()).hexdigest()
                    if content_hash not in seen_hashes:
                        results.append(vector_result)
                        seen_hashes.add(content_hash)
                
                logger.debug(f"Found {len(vector_results)} results from vector DB")
            except Exception as e:
                logger.error(f"Error querying vector DB: {e}")
        
        # Sort by timestamp (most recent first) and limit results
        results.sort(key=lambda x: x.get("ts", ""), reverse=True)
        return results[:recent_n]
    
    async def _query_vector_db(
        self,
        topic: str,
        recent_n: int,
        min_score: Optional[float],
        session_id: Optional[str],
        user_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Query vector database for semantic search."""
        threshold = self.min_similarity_score if min_score is None else float(min_score)
        
        def _blocking_query():
            try:
                qvec = self._embeddings.embed_query(topic)
                results = (
                    self._table.search(qvec)  # type: ignore[attr-defined]
                    .metric("cosine")
                    .limit(recent_n * 2)  # Get more to filter
                    .to_list()
                )
                
                filtered_results = []
                for item in results:
                    score = item.get("score", 1.0)
                    if score is None or score >= threshold:
                        # Apply filters
                        if session_id and item.get("session_id") != session_id:
                            continue
                        if user_id and item.get("user_id") != user_id:
                            continue
                        
                        filtered_results.append({
                            "ts": item.get("ts", ""),
                            "user": item.get("user", ""),
                            "text": item.get("text", ""),
                            "source": "vector_db",
                            "score": score,
                            "session_id": item.get("session_id"),
                            "user_id": item.get("user_id")
                        })
                
                return filtered_results[:recent_n]
            
            except Exception as exc:
                logger.warning("Vector semantic query failed: %s", exc)
                return []
        
        return await asyncio.get_event_loop().run_in_executor(None, _blocking_query)
    
    def _get_recent_from_memory(self, n: int) -> List[Dict[str, Any]]:
        """Get recent messages from in-memory storage."""
        recent = list(reversed(self._history[-n:]))
        return [
            {
                "ts": msg.get("ts", ""),
                "user": msg.get("user", ""),
                "text": msg.get("text", ""),
                "source": "memory",
                "session_id": msg.get("session_id"),
                "user_id": msg.get("user_id")
            }
            for msg in recent
        ]
    
    async def get_conversation_summary(
        self,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get a summary of a conversation session."""
        if not (self.structured_enabled and self.db_manager):
            return {}
        
        try:
            history = await self.db_manager.get_conversation_history(
                session_id=session_id,
                limit=100,
                user_id=user_id
            )
            
            if not history:
                return {}
            
            # Calculate summary statistics
            total_messages = len(history)
            user_messages = len([h for h in history if h["role"] == "user"])
            assistant_messages = len([h for h in history if h["role"] == "assistant"])
            
            # Calculate average response time
            response_times = [h["response_time"] for h in history if h.get("response_time")]
            avg_response_time = sum(response_times) / len(response_times) if response_times else None
            
            # Get time span
            first_message = min(history, key=lambda x: x["created_at"])
            last_message = max(history, key=lambda x: x["created_at"])
            
            # Count models/providers used
            models_used = set(h["model_used"] for h in history if h.get("model_used"))
            providers_used = set(h["provider_used"] for h in history if h.get("provider_used"))
            
            return {
                "session_id": session_id,
                "user_id": user_id,
                "total_messages": total_messages,
                "user_messages": user_messages,
                "assistant_messages": assistant_messages,
                "avg_response_time": avg_response_time,
                "first_message": first_message["created_at"],
                "last_message": last_message["created_at"],
                "models_used": list(models_used),
                "providers_used": list(providers_used),
                "duration": (last_message["created_at"] - first_message["created_at"]).total_seconds()
            }
        
        except Exception as e:
            logger.error(f"Error generating conversation summary: {e}")
            return {}
    
    async def clear_memory(self, session_id: Optional[str] = None, user_id: Optional[str] = None):
        """Clear memory (both vector and structured storage)."""
        # Clear in-memory history
        if session_id is None:
            self._history.clear()
        else:
            self._history = [
                h for h in self._history
                if h.get("session_id") != session_id or (user_id and h.get("user_id") != user_id)
            ]
        
        # Clear vector storage
        if self.enabled and self.persist and self._db is not None:
            try:
                if session_id is None:
                    # Clear entire collection
                    if self._table is not None:
                        self._db.drop_table(self.collection)
                        self._table = None
                else:
                    # TODO: Implement selective deletion based on session_id
                    logger.warning("Selective vector storage clearing not implemented")
            except Exception as exc:
                logger.warning("Failed to clear vector storage: %s", exc)
        
        # Clear structured storage would require additional database operations
        # For now, we log this as a feature to implement
        if session_id:
            logger.info(f"Selective clearing of structured storage for session {session_id} not implemented")
        
        logger.info("Memory cleared")
    
    # Backward compatibility methods
    def store(self, role: str, text: str) -> None:
        """Backward compatible store method."""
        asyncio.create_task(self.store_message(role, text))
    
    def session_history(self) -> List[dict]:
        """Get in-memory session history for backward compatibility."""
        return list(self._history)
    
    async def get_similar_messages(
        self,
        query: str,
        top_k: int = 5,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get similar messages (backward compatibility)."""
        return await self.query_memory(
            topic=query,
            recent_n=top_k,
            session_id=session_id,
            user_id=user_id
        )
    
    def get_recent_messages(self, n: int = 5) -> List[Dict[str, Any]]:
        """Get recent messages (backward compatibility)."""
        # For backward compatibility, run async method synchronously
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.query_memory(recent_n=n))
        except RuntimeError:
            return asyncio.run(self.query_memory(recent_n=n))