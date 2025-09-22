# core/brain.py
"""
core.brain — Enhanced LLM support with multiple provider backends.
- Supports multiple LLM providers (Ollama, OpenAI, Anthropic, etc.)
- Streams responses token by token for real-time voice interaction.
- Injects personality through system prompts.
- Provides fallback support between providers.
"""
import asyncio
import logging
from typing import AsyncGenerator, List, Dict, Any

# Local Imports
from core.config import settings
from core.personality import get_system_prompt
from core.llm_providers.factory import LLMProviderManager, LLMProviderFactory
try:
    from core.knowledge_manager import KnowledgeManager  # optional use
except Exception:
    KnowledgeManager = None  # type: ignore

logger = logging.getLogger("nia.core.brain")

class Brain:
    def __init__(self, model: str, timeout: int):
        self.model_name = model
        self.timeout = timeout
        
        # Load system prompt from personality system (with fallback to settings)
        self.system_prompt = get_system_prompt("default")
        if not self.system_prompt:
            self.system_prompt = settings["brain"].get("system_prompt", "")
        
        # Initialize LLM provider manager
        self.provider_manager = self._initialize_providers()
        
        # Optional knowledge manager
        self.knowledge_enabled = bool(settings.get("knowledge", {}).get("enabled", True))
        self.knowledge_top_k = int(settings.get("knowledge", {}).get("top_k", 5))
        self.knowledge_mgr = KnowledgeManager() if self.knowledge_enabled and KnowledgeManager else None

        logger.info("Brain initialized with LLM providers")
        logger.info("System prompt loaded: %s", self.system_prompt[:50] + "..." if len(self.system_prompt) > 50 else self.system_prompt)
    
    def _initialize_providers(self) -> LLMProviderManager:
        """Initialize LLM providers based on configuration."""
        brain_config = settings.get("brain", {})
        
        # Primary provider configuration
        primary_provider_type = brain_config.get("provider", "ollama")
        primary_config = {
            "type": primary_provider_type,
            "model": self.model_name,
            "timeout": self.timeout,
            "temperature": brain_config.get("temperature", 0.7),
            "max_tokens": brain_config.get("max_tokens", 2000),
            **brain_config.get("provider_config", {})
        }
        
        # Fallback providers configuration
        fallback_configs = []
        fallback_settings = brain_config.get("fallback_providers", [])
        
        for fallback in fallback_settings:
            fallback_config = {
                "type": fallback["provider"],
                "model": fallback.get("model", "default"),
                "timeout": self.timeout,
                "temperature": brain_config.get("temperature", 0.7),
                "max_tokens": brain_config.get("max_tokens", 2000),
                **fallback.get("config", {})
            }
            fallback_configs.append(fallback_config)
        
        # Add Ollama as fallback if not already primary
        if primary_provider_type != "ollama" and not any(f["type"] == "ollama" for f in fallback_configs):
            fallback_configs.append({
                "type": "ollama",
                "model": "qwen3:4b",
                "timeout": self.timeout,
                "temperature": brain_config.get("temperature", 0.7),
                "max_tokens": brain_config.get("max_tokens", 2000)
            })
        
        return LLMProviderManager(primary_config, fallback_configs if fallback_configs else None)

    async def generate_stream(self, prompt: str, context_snippets: list[str] | None = None) -> AsyncGenerator[dict, None]:
        """
        Streams the LLM response token by token for real-time voice interaction.
        Injects personality through system prompts for consistent voice and tone.
        """
        logger.info("Generating streaming response for prompt: '%s'", prompt)
        
        try:
            # Build messages in standard format
            messages = []
            
            # Add system prompt if available for personality
            if self.system_prompt:
                messages.append({"role": "system", "content": self.system_prompt})
            
            # Retrieve knowledge docs if enabled
            knowledge_snippets: List[str] = []
            if self.knowledge_mgr is not None and self.knowledge_enabled:
                try:
                    docs = self.knowledge_mgr.query(prompt, top_k=self.knowledge_top_k)
                    knowledge_snippets = [f"{d.get('source', d.get('name',''))}: {d.get('text','')}" for d in docs]
                except Exception:
                    knowledge_snippets = []

            # Add memory/context as a preface if provided
            if context_snippets:
                context_text = "\n".join(f"- {s}" for s in context_snippets)
                messages.append({"role": "user", "content": f"Context to consider (recent related notes):\n{context_text}"})
            
            # Add knowledge snippets if available
            if knowledge_snippets:
                knowledge_text = "\n".join(f"- {s}" for s in knowledge_snippets)
                messages.append({"role": "user", "content": f"Relevant knowledge base excerpts:\n{knowledge_text}"})
            
            # Add user prompt last
            messages.append({"role": "user", "content": prompt})
            
            # Stream the response using the provider manager
            async for chunk in self.provider_manager.generate_stream(messages):
                yield chunk
            
            logger.info("Streaming response completed successfully")

        except Exception as e:
            logger.exception("An error occurred while streaming LLM response.")
            yield {"error": f"LLM Error: {e}", "done": True}

    def generate(self, prompt: str) -> str:
        """
        Synchronous wrapper for generate_stream for console interface compatibility.
        Collects the full response and returns it as a string.
        """
        
        async def _collect_response():
            full_response = ""
            async for chunk in self.generate_stream(prompt):
                if "response" in chunk and chunk["response"]:
                    full_response += chunk["response"]
                elif chunk.get("done"):
                    break
                elif "error" in chunk:
                    return f"[ERROR] {chunk['error']}"
            return full_response
        
        # Run the async function in a new event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an event loop, we need to use a different approach
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _collect_response())
                    return future.result()
            else:
                return loop.run_until_complete(_collect_response())
        except RuntimeError:
            # No event loop exists, create a new one
            return asyncio.run(_collect_response())

    async def close(self):
        """Placeholder for any future cleanup, like closing client sessions."""
        logger.info("Brain shutting down.")
        pass

    def health_check(self) -> dict:
        """Returns a health check dictionary reflecting the new architecture."""
        try:
            # Get current provider info
            current_provider = self.provider_manager.get_current_provider()
            provider_name = current_provider.__class__.__name__ if current_provider else "Unknown"
            
            return {
                "llm_provider": f"Multi-provider system ({provider_name})",
                "configured_model": self.model_name,
                "streaming_enabled": True,
                "personality_loaded": bool(self.system_prompt),
                "providers_available": len(self.provider_manager.providers),
                "current_provider_index": self.provider_manager.current_provider_index
            }
        except Exception as e:
            return {
                "llm_provider": "Multi-provider system (Error)",
                "configured_model": self.model_name,
                "streaming_enabled": True,
                "personality_loaded": bool(self.system_prompt),
                "error": str(e)
            }

