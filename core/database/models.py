"""
Database models for NIA.

Defines the data structures for storing conversations, users, analytics, and other structured data.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class User(Base):
    """User profiles and authentication."""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # User preferences
    preferences = Column(JSON, default=dict)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    analytics = relationship("AnalyticsEvent", back_populates="user")


class Conversation(Base):
    """Structured conversation storage."""
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    session_id = Column(String(255), nullable=False)
    
    # Message content
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    response_time = Column(Float, nullable=True)  # Response time in seconds
    model_used = Column(String(255), nullable=True)
    provider_used = Column(String(100), nullable=True)
    
    # Context information
    context_snippets = Column(JSON, default=list)
    knowledge_snippets = Column(JSON, default=list)
    
    # Quality metrics
    confidence_score = Column(Float, nullable=True)
    user_rating = Column(Integer, nullable=True)  # 1-5 rating
    
    # Relationships
    user = relationship("User", back_populates="conversations")


class KnowledgeItem(Base):
    """Structured knowledge base items."""
    __tablename__ = "knowledge_items"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    
    # Classification
    category = Column(String(100), nullable=True)
    tags = Column(JSON, default=list)
    source = Column(String(255), nullable=True)  # file, web, manual
    source_path = Column(String(1000), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, nullable=True)
    
    # Content metrics
    word_count = Column(Integer, default=0)
    content_hash = Column(String(64), nullable=True)  # For detecting changes
    
    # Quality and relevance
    relevance_score = Column(Float, default=0.0)
    user_feedback = Column(JSON, default=dict)


class AnalyticsEvent(Base):
    """System analytics and usage tracking."""
    __tablename__ = "analytics_events"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    session_id = Column(String(255), nullable=False)
    
    # Event information
    event_type = Column(String(100), nullable=False)  # interaction, error, performance
    event_name = Column(String(255), nullable=False)
    
    # Event data
    event_data = Column(JSON, default=dict)
    
    # Performance metrics
    duration = Column(Float, nullable=True)
    memory_usage = Column(Float, nullable=True)
    cpu_usage = Column(Float, nullable=True)
    
    # Context
    interface_type = Column(String(50), nullable=True)  # voice, console, api
    provider_used = Column(String(100), nullable=True)
    model_used = Column(String(255), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="analytics")


class SystemHealth(Base):
    """System health and performance monitoring."""
    __tablename__ = "system_health"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Health metrics
    cpu_usage = Column(Float, nullable=False)
    memory_usage = Column(Float, nullable=False)
    disk_usage = Column(Float, nullable=False)
    
    # Component health
    llm_provider_status = Column(JSON, default=dict)
    database_status = Column(String(50), default="healthy")
    cache_status = Column(String(50), default="healthy")
    
    # Performance metrics
    avg_response_time = Column(Float, nullable=True)
    total_requests = Column(Integer, default=0)
    error_rate = Column(Float, default=0.0)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)


class Configuration(Base):
    """Dynamic configuration storage."""
    __tablename__ = "configuration"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String(255), unique=True, nullable=False)
    value = Column(JSON, nullable=False)
    
    # Metadata
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(255), nullable=True)
    
    # Validation
    value_type = Column(String(50), nullable=False)  # string, int, float, bool, dict, list
    is_sensitive = Column(Boolean, default=False)  # For API keys, passwords, etc.


class Plugin(Base):
    """Plugin management and configuration."""
    __tablename__ = "plugins"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), unique=True, nullable=False)
    version = Column(String(50), nullable=False)
    
    # Plugin information
    description = Column(Text, nullable=True)
    author = Column(String(255), nullable=True)
    status = Column(String(50), default="inactive")  # active, inactive, error
    
    # Configuration
    config = Column(JSON, default=dict)
    dependencies = Column(JSON, default=list)
    
    # Metadata
    installed_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    
    # Performance
    avg_execution_time = Column(Float, nullable=True)


class APIKey(Base):
    """API key management for external access."""
    __tablename__ = "api_keys"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key_hash = Column(String(255), unique=True, nullable=False)  # Hashed API key
    name = Column(String(255), nullable=False)
    
    # Access control
    is_active = Column(Boolean, default=True)
    permissions = Column(JSON, default=list)  # List of allowed endpoints/actions
    rate_limit = Column(Integer, default=60)  # Requests per minute
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    created_by = Column(String(255), nullable=True)