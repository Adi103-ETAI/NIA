"""
LLM Provider Factory for NIA.

Creates and manages different LLM providers based on configuration.
"""

from typing import Dict, Any, Type, Optional
import logging
from .base import LLMProvider
from .ollama_provider import OllamaProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider

logger = logging.getLogger("nia.core.llm_providers.factory")

# Registry of available providers
PROVIDER_REGISTRY: Dict[str, Type[LLMProvider]] = {
    "ollama": OllamaProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
}


class LLMProviderFactory:
    """Factory for creating LLM providers."""
    
    @staticmethod
    def create_provider(provider_type: str, config: Dict[str, Any]) -> LLMProvider:
        """
        Create an LLM provider instance.
        
        Args:
            provider_type: Type of provider ("ollama", "openai", "anthropic")
            config: Provider configuration
            
        Returns:
            LLMProvider instance
            
        Raises:
            ValueError: If provider type is not supported
            ImportError: If required dependencies are missing
        """
        if provider_type not in PROVIDER_REGISTRY:
            available = ", ".join(PROVIDER_REGISTRY.keys())
            raise ValueError(f"Unsupported provider type '{provider_type}'. Available: {available}")
        
        provider_class = PROVIDER_REGISTRY[provider_type]
        
        try:
            provider = provider_class(config)
            logger.info(f"Created {provider_type} provider with model: {provider.model_name}")
            return provider
        except ImportError as e:
            logger.error(f"Failed to create {provider_type} provider due to missing dependencies: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to create {provider_type} provider: {e}")
            raise
    
    @staticmethod
    def get_available_providers() -> list[str]:
        """Get list of available provider types."""
        return list(PROVIDER_REGISTRY.keys())
    
    @staticmethod
    def register_provider(name: str, provider_class: Type[LLMProvider]):
        """
        Register a custom provider.
        
        Args:
            name: Provider name
            provider_class: Provider class that inherits from LLMProvider
        """
        if not issubclass(provider_class, LLMProvider):
            raise ValueError("Provider class must inherit from LLMProvider")
        
        PROVIDER_REGISTRY[name] = provider_class
        logger.info(f"Registered custom provider: {name}")


class LLMProviderManager:
    """Manages multiple LLM providers with fallback support."""
    
    def __init__(self, primary_config: Dict[str, Any], fallback_configs: Optional[list[Dict[str, Any]]] = None):
        """
        Initialize provider manager.
        
        Args:
            primary_config: Primary provider configuration
            fallback_configs: Optional list of fallback provider configurations
        """
        self.providers: list[LLMProvider] = []
        self.current_provider_index = 0
        
        # Create primary provider
        try:
            primary_provider = LLMProviderFactory.create_provider(
                primary_config["type"], 
                primary_config
            )
            self.providers.append(primary_provider)
            logger.info(f"Primary provider initialized: {primary_config['type']}")
        except Exception as e:
            logger.error(f"Failed to initialize primary provider: {e}")
        
        # Create fallback providers
        if fallback_configs:
            for fallback_config in fallback_configs:
                try:
                    fallback_provider = LLMProviderFactory.create_provider(
                        fallback_config["type"],
                        fallback_config
                    )
                    self.providers.append(fallback_provider)
                    logger.info(f"Fallback provider initialized: {fallback_config['type']}")
                except Exception as e:
                    logger.warning(f"Failed to initialize fallback provider {fallback_config['type']}: {e}")
        
        if not self.providers:
            raise RuntimeError("No LLM providers could be initialized")
    
    async def generate_stream(self, messages: list[Dict[str, str]], **kwargs):
        """Generate streaming response with fallback support."""
        for i, provider in enumerate(self.providers):
            try:
                self.current_provider_index = i
                async for chunk in provider.generate_stream(messages, **kwargs):
                    yield chunk
                return  # Success, no need to try fallbacks
            except Exception as e:
                logger.warning(f"Provider {provider.__class__.__name__} failed: {e}")
                if i == len(self.providers) - 1:
                    # Last provider failed
                    yield {"error": f"All providers failed. Last error: {e}", "done": True}
                    return
                logger.info(f"Falling back to next provider...")
    
    async def generate(self, messages: list[Dict[str, str]], **kwargs) -> str:
        """Generate non-streaming response with fallback support."""
        for i, provider in enumerate(self.providers):
            try:
                self.current_provider_index = i
                response = await provider.generate(messages, **kwargs)
                return response
            except Exception as e:
                logger.warning(f"Provider {provider.__class__.__name__} failed: {e}")
                if i == len(self.providers) - 1:
                    # Last provider failed
                    return f"All providers failed. Last error: {e}"
                logger.info(f"Falling back to next provider...")
        
        return "No providers available"
    
    async def health_check_all(self) -> Dict[str, Any]:
        """Check health of all providers."""
        health_results = {}
        
        for i, provider in enumerate(self.providers):
            provider_name = f"{provider.__class__.__name__}_{i}"
            try:
                health = await provider.health_check()
                health_results[provider_name] = health
            except Exception as e:
                health_results[provider_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return {
            "current_provider_index": self.current_provider_index,
            "total_providers": len(self.providers),
            "providers": health_results
        }
    
    def get_current_provider(self) -> Optional[LLMProvider]:
        """Get the currently active provider."""
        if self.providers:
            return self.providers[self.current_provider_index]
        return None