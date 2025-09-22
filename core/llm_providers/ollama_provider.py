"""
Ollama Provider for NIA (existing local LLM support).

Maintains compatibility with existing Ollama integration while fitting new provider architecture.
"""

from typing import AsyncGenerator, Dict, Any, List
import logging
from .base import LLMProvider

try:
    from langchain_ollama import ChatOllama
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    ChatOllama = None

try:
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
    LANGCHAIN_CORE_AVAILABLE = True
except ImportError:
    LANGCHAIN_CORE_AVAILABLE = False
    HumanMessage = SystemMessage = AIMessage = None

logger = logging.getLogger("nia.core.llm_providers.ollama")


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        if not LANGCHAIN_AVAILABLE or not LANGCHAIN_CORE_AVAILABLE:
            raise ImportError("LangChain libraries not available. Install with: pip install langchain langchain-ollama")
        
        # Model configuration
        self.model_name = config.get("model", "qwen3:4b")
        self.base_url = config.get("base_url", "http://localhost:11434")
        
        # Initialize LangChain ChatOllama
        self.llm = ChatOllama(
            model=self.model_name,
            base_url=self.base_url,
            temperature=self.temperature,
            streaming=True,
            timeout=self.timeout
        )
        
        logger.info(f"Ollama provider initialized with model: {self.model_name}")
    
    def _convert_to_langchain_messages(self, messages: List[Dict[str, str]]):
        """Convert standard message format to LangChain messages."""
        langchain_messages = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "user":
                langchain_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            else:
                # Default to human message
                langchain_messages.append(HumanMessage(content=content))
        
        return langchain_messages
    
    async def generate_stream(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate streaming response from Ollama."""
        try:
            langchain_messages = self._convert_to_langchain_messages(messages)
            
            # Handle thinking mode filtering (existing NIA feature)
            in_thinking_mode = False
            
            async for chunk in self.llm.astream(langchain_messages):
                if hasattr(chunk, 'content') and chunk.content:
                    content = chunk.content
                    
                    # Check if we're entering thinking mode
                    if '<think>' in content:
                        in_thinking_mode = True
                        content = content.split('<think>')[0]
                    
                    # Check if we're exiting thinking mode
                    if '</think>' in content:
                        in_thinking_mode = False
                        content = content.split('</think>')[-1]
                    
                    # Only yield content if we're not in thinking mode and there's actual content
                    if not in_thinking_mode and content.strip():
                        yield {"response": content, "done": False}
                        logger.debug("Ollama streamed token: %s", content)
            
            # Signal completion
            yield {"response": "", "done": True}
            logger.info("Ollama streaming response completed")
                    
        except Exception as e:
            logger.exception("Error in Ollama streaming generation")
            yield {"error": f"Ollama Error: {e}", "done": True}
    
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate non-streaming response from Ollama."""
        try:
            full_response = ""
            async for chunk in self.generate_stream(messages, **kwargs):
                if "response" in chunk and chunk["response"]:
                    full_response += chunk["response"]
                elif chunk.get("done"):
                    break
                elif "error" in chunk:
                    return chunk["error"]
            return full_response
            
        except Exception as e:
            logger.exception("Error in Ollama generation")
            return f"Ollama Error: {e}"
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Ollama health."""
        try:
            # Simple test request
            test_messages = [{"role": "user", "content": "Hello"}]
            response = await self.generate(test_messages)
            
            return {
                "status": "healthy" if response and "Error" not in response else "unhealthy",
                "provider": "Ollama",
                "model": self.model_name,
                "base_url": self.base_url,
                "api_available": True
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "Ollama",
                "model": self.model_name,
                "base_url": self.base_url,
                "api_available": False,
                "error": str(e)
            }
    
    def get_available_models(self) -> List[str]:
        """Get available Ollama models."""
        # Common Ollama models - in practice you might query the API
        return [
            "qwen3:4b",
            "phi4-mini:3.8b", 
            "zephyr:7b",
            "llama3.2:3b",
            "llama3.2:1b",
            "mistral:7b",
            "codellama:7b",
            "deepseek-coder:6.7b"
        ]