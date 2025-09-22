"""
Anthropic Claude API Provider for NIA.

Supports Anthropic Claude models with streaming and non-streaming responses.
"""

from typing import AsyncGenerator, Dict, Any, List
import logging
import asyncio
from .base import LLMProvider

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None

logger = logging.getLogger("nia.core.llm_providers.anthropic")


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic library not available. Install with: pip install anthropic")
        
        self.api_key = config.get("api_key")
        if not self.api_key:
            raise ValueError("Anthropic API key is required")
        
        # Initialize Anthropic client
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
        
        # Model configuration
        self.model_name = config.get("model", "claude-3-5-sonnet-20241022")
        self.max_tokens = config.get("max_tokens", 2000)
        
        logger.info(f"Anthropic provider initialized with model: {self.model_name}")
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> tuple[str, List[Dict[str, str]]]:
        """Convert messages to Anthropic format (system message separate)."""
        system_message = ""
        claude_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                claude_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        return system_message, claude_messages
    
    async def generate_stream(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate streaming response from Anthropic API."""
        try:
            system_message, claude_messages = self._convert_messages(messages)
            
            # Streaming request
            async with self.client.messages.stream(
                model=self.model_name,
                messages=claude_messages,
                system=system_message if system_message else anthropic.NOT_GIVEN,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **kwargs
            ) as stream:
                async for text in stream.text_stream:
                    if text:
                        yield {"response": text, "done": False}
            
            # Signal completion
            yield {"response": "", "done": True}
                    
        except Exception as e:
            logger.exception("Error in Anthropic streaming generation")
            yield {"error": f"Anthropic Error: {e}", "done": True}
    
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate non-streaming response from Anthropic API."""
        try:
            system_message, claude_messages = self._convert_messages(messages)
            
            response = await self.client.messages.create(
                model=self.model_name,
                messages=claude_messages,
                system=system_message if system_message else anthropic.NOT_GIVEN,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **kwargs
            )
            
            # Extract text from response
            content = ""
            for block in response.content:
                if block.type == "text":
                    content += block.text
            
            return content
            
        except Exception as e:
            logger.exception("Error in Anthropic generation")
            return f"Anthropic Error: {e}"
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Anthropic API health."""
        try:
            # Simple test request
            response = await self.client.messages.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            
            return {
                "status": "healthy",
                "provider": "Anthropic",
                "model": self.model_name,
                "api_available": True
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "Anthropic",
                "model": self.model_name,
                "api_available": False,
                "error": str(e)
            }
    
    def get_available_models(self) -> List[str]:
        """Get available Anthropic models."""
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022", 
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]