"""
OpenAI API Provider for NIA.

Supports OpenAI GPT models with streaming and non-streaming responses.
"""

from typing import AsyncGenerator, Dict, Any, List
import logging
import asyncio
from .base import LLMProvider

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None

logger = logging.getLogger("nia.core.llm_providers.openai")


class OpenAIProvider(LLMProvider):
    """OpenAI API provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not available. Install with: pip install openai")
        
        self.api_key = config.get("api_key")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.base_url = config.get("base_url")  # For custom endpoints
        self.organization = config.get("organization")
        
        # Initialize OpenAI client
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        if self.organization:
            client_kwargs["organization"] = self.organization
            
        self.client = AsyncOpenAI(**client_kwargs)
        
        # Model configuration
        self.model_name = config.get("model", "gpt-3.5-turbo")
        self.max_tokens = config.get("max_tokens", 2000)
        
        logger.info(f"OpenAI provider initialized with model: {self.model_name}")
    
    async def generate_stream(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate streaming response from OpenAI API."""
        try:
            # Convert messages to OpenAI format
            openai_messages = []
            for msg in messages:
                openai_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Streaming request
            stream = await self.client.chat.completions.create(
                model=self.model_name,
                messages=openai_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield {"response": content, "done": False}
                    
                # Check if stream is finished
                if chunk.choices and chunk.choices[0].finish_reason:
                    yield {"response": "", "done": True}
                    return
                    
        except Exception as e:
            logger.exception("Error in OpenAI streaming generation")
            yield {"error": f"OpenAI Error: {e}", "done": True}
    
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate non-streaming response from OpenAI API."""
        try:
            # Convert messages to OpenAI format
            openai_messages = []
            for msg in messages:
                openai_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=openai_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=False,
                **kwargs
            )
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            logger.exception("Error in OpenAI generation")
            return f"OpenAI Error: {e}"
    
    async def health_check(self) -> Dict[str, Any]:
        """Check OpenAI API health."""
        try:
            # Simple test request
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            
            return {
                "status": "healthy",
                "provider": "OpenAI",
                "model": self.model_name,
                "api_available": True
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "OpenAI",
                "model": self.model_name,
                "api_available": False,
                "error": str(e)
            }
    
    def get_available_models(self) -> List[str]:
        """Get available OpenAI models."""
        # Common OpenAI models - in practice you might query the API
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-0125"
        ]