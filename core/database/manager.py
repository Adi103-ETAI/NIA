"""
Database Manager for NIA.

Handles database connections, migrations, and provides a unified interface for data operations.
"""

import logging
import os
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from core.config import settings
from .models import Base, User, Conversation, KnowledgeItem, AnalyticsEvent, SystemHealth, Configuration

logger = logging.getLogger("nia.core.database.manager")


class DatabaseManager:
    """Main database manager for NIA."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or settings.get("database", {})
        
        # Database connections
        self.engine = None
        self.async_engine = None
        self.SessionLocal = None
        self.AsyncSessionLocal = None
        
        # Connection status
        self.is_connected = False
        
        # Initialize connections
        self._initialize_connections()
    
    def _initialize_connections(self):
        """Initialize database connections based on configuration."""
        primary_config = self.config.get("primary", {})
        db_type = primary_config.get("type", "sqlite")
        
        try:
            if db_type == "sqlite":
                self._initialize_sqlite(primary_config)
            elif db_type == "postgresql":
                self._initialize_postgresql(primary_config)
            elif db_type == "mysql":
                self._initialize_mysql(primary_config)
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
            
            # Create tables if they don't exist
            self._create_tables()
            self.is_connected = True
            logger.info(f"Database manager initialized with {db_type}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            self.is_connected = False
    
    def _initialize_sqlite(self, config: Dict[str, Any]):
        """Initialize SQLite database."""
        db_path = config.get("connection", {}).get("path", "data/nia.db")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Create engine
        database_url = f"sqlite:///{db_path}"
        self.engine = create_engine(
            database_url,
            echo=False,
            pool_pre_ping=True
        )
        
        # Create async engine for async operations
        async_database_url = f"sqlite+aiosqlite:///{db_path}"
        self.async_engine = create_async_engine(
            async_database_url,
            echo=False
        )
        
        # Create session makers
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.AsyncSessionLocal = async_sessionmaker(bind=self.async_engine)
    
    def _initialize_postgresql(self, config: Dict[str, Any]):
        """Initialize PostgreSQL database."""
        conn_config = config.get("connection", {})
        pool_config = config.get("pool", {})
        
        # Build connection URL
        database_url = (
            f"postgresql://{conn_config['username']}:{conn_config['password']}"
            f"@{conn_config['host']}:{conn_config['port']}/{conn_config['database']}"
        )
        
        # Create engine with connection pooling
        self.engine = create_engine(
            database_url,
            echo=False,
            pool_size=pool_config.get("min_connections", 5),
            max_overflow=pool_config.get("max_connections", 20) - pool_config.get("min_connections", 5),
            pool_timeout=pool_config.get("timeout", 30),
            pool_pre_ping=True
        )
        
        # Create async engine
        async_database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        self.async_engine = create_async_engine(
            async_database_url,
            echo=False,
            pool_size=pool_config.get("min_connections", 5),
            max_overflow=pool_config.get("max_connections", 20) - pool_config.get("min_connections", 5),
        )
        
        # Create session makers
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.AsyncSessionLocal = async_sessionmaker(bind=self.async_engine)
    
    def _initialize_mysql(self, config: Dict[str, Any]):
        """Initialize MySQL database."""
        conn_config = config.get("connection", {})
        pool_config = config.get("pool", {})
        
        # Build connection URL
        database_url = (
            f"mysql+pymysql://{conn_config['username']}:{conn_config['password']}"
            f"@{conn_config['host']}:{conn_config['port']}/{conn_config['database']}"
        )
        
        # Create engine with connection pooling
        self.engine = create_engine(
            database_url,
            echo=False,
            pool_size=pool_config.get("min_connections", 5),
            max_overflow=pool_config.get("max_connections", 20) - pool_config.get("min_connections", 5),
            pool_timeout=pool_config.get("timeout", 30),
            pool_pre_ping=True
        )
        
        # Create async engine
        async_database_url = database_url.replace("mysql+pymysql://", "mysql+aiomysql://")
        self.async_engine = create_async_engine(
            async_database_url,
            echo=False,
            pool_size=pool_config.get("min_connections", 5),
            max_overflow=pool_config.get("max_connections", 20) - pool_config.get("min_connections", 5),
        )
        
        # Create session makers
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.AsyncSessionLocal = async_sessionmaker(bind=self.async_engine)
    
    def _create_tables(self):
        """Create database tables if they don't exist."""
        if self.engine:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created/verified")
    
    @asynccontextmanager
    async def get_async_session(self):
        """Get an async database session."""
        if not self.AsyncSessionLocal:
            raise RuntimeError("Async database session not initialized")
        
        async with self.AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    def get_session(self) -> Session:
        """Get a synchronous database session."""
        if not self.SessionLocal:
            raise RuntimeError("Database session not initialized")
        
        return self.SessionLocal()
    
    # Conversation methods
    async def store_conversation(
        self,
        role: str,
        content: str,
        session_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a conversation message."""
        async with self.get_async_session() as session:
            conversation = Conversation(
                user_id=user_id,
                session_id=session_id,
                role=role,
                content=content,
                response_time=metadata.get("response_time") if metadata else None,
                model_used=metadata.get("model_used") if metadata else None,
                provider_used=metadata.get("provider_used") if metadata else None,
                context_snippets=metadata.get("context_snippets", []) if metadata else [],
                knowledge_snippets=metadata.get("knowledge_snippets", []) if metadata else [],
                confidence_score=metadata.get("confidence_score") if metadata else None
            )
            
            session.add(conversation)
            await session.flush()
            return conversation.id
    
    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 50,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        async with self.get_async_session() as session:
            query = session.query(Conversation).filter(
                Conversation.session_id == session_id
            )
            
            if user_id:
                query = query.filter(Conversation.user_id == user_id)
            
            conversations = query.order_by(
                Conversation.created_at.desc()
            ).limit(limit).all()
            
            return [
                {
                    "id": conv.id,
                    "role": conv.role,
                    "content": conv.content,
                    "created_at": conv.created_at,
                    "response_time": conv.response_time,
                    "model_used": conv.model_used,
                    "provider_used": conv.provider_used
                }
                for conv in reversed(conversations)
            ]
    
    # Knowledge management methods
    async def store_knowledge_item(
        self,
        title: str,
        content: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        source: Optional[str] = None,
        source_path: Optional[str] = None
    ) -> str:
        """Store a knowledge base item."""
        async with self.get_async_session() as session:
            knowledge_item = KnowledgeItem(
                title=title,
                content=content,
                category=category,
                tags=tags or [],
                source=source,
                source_path=source_path,
                word_count=len(content.split())
            )
            
            session.add(knowledge_item)
            await session.flush()
            return knowledge_item.id
    
    async def search_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search knowledge base items."""
        async with self.get_async_session() as session:
            # Basic text search - can be enhanced with full-text search
            query_filter = KnowledgeItem.content.contains(query) | KnowledgeItem.title.contains(query)
            
            db_query = session.query(KnowledgeItem).filter(query_filter)
            
            if category:
                db_query = db_query.filter(KnowledgeItem.category == category)
            
            if tags:
                # Simple tag filtering - can be enhanced with proper JSON queries
                for tag in tags:
                    db_query = db_query.filter(KnowledgeItem.tags.contains([tag]))
            
            knowledge_items = db_query.order_by(
                KnowledgeItem.relevance_score.desc()
            ).limit(limit).all()
            
            return [
                {
                    "id": item.id,
                    "title": item.title,
                    "content": item.content,
                    "category": item.category,
                    "tags": item.tags,
                    "created_at": item.created_at,
                    "relevance_score": item.relevance_score
                }
                for item in knowledge_items
            ]
    
    # Analytics methods
    async def log_analytics_event(
        self,
        event_type: str,
        event_name: str,
        session_id: str,
        user_id: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None,
        duration: Optional[float] = None
    ) -> str:
        """Log an analytics event."""
        async with self.get_async_session() as session:
            analytics_event = AnalyticsEvent(
                user_id=user_id,
                session_id=session_id,
                event_type=event_type,
                event_name=event_name,
                event_data=event_data or {},
                duration=duration
            )
            
            session.add(analytics_event)
            await session.flush()
            return analytics_event.id
    
    async def get_analytics_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get analytics summary for a date range."""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        async with self.get_async_session() as session:
            # Total events
            total_events = session.query(AnalyticsEvent).filter(
                AnalyticsEvent.created_at.between(start_date, end_date)
            ).count()
            
            # Event types breakdown
            event_types = session.query(
                AnalyticsEvent.event_type,
                text("COUNT(*) as count")
            ).filter(
                AnalyticsEvent.created_at.between(start_date, end_date)
            ).group_by(AnalyticsEvent.event_type).all()
            
            # Average response time
            avg_duration = session.query(
                text("AVG(duration) as avg_duration")
            ).filter(
                AnalyticsEvent.created_at.between(start_date, end_date),
                AnalyticsEvent.duration.is_not(None)
            ).scalar()
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "total_events": total_events,
                "event_types": {et[0]: et[1] for et in event_types},
                "avg_duration": float(avg_duration) if avg_duration else None
            }
    
    # System health methods
    async def record_system_health(
        self,
        cpu_usage: float,
        memory_usage: float,
        disk_usage: float,
        llm_provider_status: Dict[str, Any],
        performance_metrics: Optional[Dict[str, Any]] = None
    ) -> str:
        """Record system health metrics."""
        async with self.get_async_session() as session:
            health_record = SystemHealth(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                llm_provider_status=llm_provider_status,
                avg_response_time=performance_metrics.get("avg_response_time") if performance_metrics else None,
                total_requests=performance_metrics.get("total_requests", 0) if performance_metrics else 0,
                error_rate=performance_metrics.get("error_rate", 0.0) if performance_metrics else 0.0
            )
            
            session.add(health_record)
            await session.flush()
            return health_record.id
    
    async def get_system_health_history(
        self,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get system health history."""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        async with self.get_async_session() as session:
            health_records = session.query(SystemHealth).filter(
                SystemHealth.created_at >= start_time
            ).order_by(SystemHealth.created_at.asc()).all()
            
            return [
                {
                    "created_at": record.created_at,
                    "cpu_usage": record.cpu_usage,
                    "memory_usage": record.memory_usage,
                    "disk_usage": record.disk_usage,
                    "llm_provider_status": record.llm_provider_status,
                    "avg_response_time": record.avg_response_time,
                    "total_requests": record.total_requests,
                    "error_rate": record.error_rate
                }
                for record in health_records
            ]
    
    # Configuration methods
    async def get_config_value(self, key: str, default=None):
        """Get a configuration value."""
        async with self.get_async_session() as session:
            config_item = session.query(Configuration).filter(
                Configuration.key == key
            ).first()
            
            return config_item.value if config_item else default
    
    async def set_config_value(
        self,
        key: str,
        value: Any,
        description: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        """Set a configuration value."""
        async with self.get_async_session() as session:
            config_item = session.query(Configuration).filter(
                Configuration.key == key
            ).first()
            
            if config_item:
                config_item.value = value
                config_item.updated_at = datetime.utcnow()
                config_item.updated_by = updated_by
                if description:
                    config_item.description = description
            else:
                config_item = Configuration(
                    key=key,
                    value=value,
                    description=description,
                    updated_by=updated_by,
                    value_type=type(value).__name__
                )
                session.add(config_item)
    
    def health_check(self) -> Dict[str, Any]:
        """Check database health."""
        try:
            if not self.is_connected:
                return {
                    "status": "unhealthy",
                    "error": "Not connected to database"
                }
            
            # Test connection
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            
            return {
                "status": "healthy",
                "database_type": self.config.get("primary", {}).get("type", "unknown"),
                "connected": True
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "connected": False
            }
    
    async def close(self):
        """Close database connections."""
        if self.engine:
            self.engine.dispose()
        if self.async_engine:
            await self.async_engine.dispose()
        
        logger.info("Database connections closed")


# Global database manager instance
db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager