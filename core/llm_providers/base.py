"""
Base LLM Provider interface for NIA.

This module defines the abstract interface that all LLM providers must implement.
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, List, Optional
import logging

logger = logging.getLogger("nia.core.llm_providers.base")


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_name = config.get("model", "default")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", None)
        self.timeout = config.get("timeout", 180)
        
    @abstractmethod
    async def generate_stream(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate streaming response from the LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            **kwargs: Additional provider-specific parameters
            
        Yields:
            Dict with 'response' (token content), 'done' (bool), and optional 'error'
        """
        pass
    
    @abstractmethod
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate non-streaming response from the LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Complete response string
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check if the provider is available and healthy.
        
        Returns:
            Dict with health status information
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Get list of available models for this provider.
        
        Returns:
            List of model names
        """
        pass
    
    def supports_streaming(self) -> bool:
        """Whether this provider supports streaming responses."""
        return True
    
    def supports_system_messages(self) -> bool:
        """Whether this provider supports system messages."""
        return True