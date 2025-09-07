# core/brain.py
"""
core.brain — Powered by LangChain + Ollama for natural conversation.
- Manages direct LLM interaction without tools for now.
- Streams responses token by token for real-time voice interaction.
- Injects personality through system prompts.
"""
import asyncio
import logging
from typing import AsyncGenerator

# LangChain Imports
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

# Local Imports
from core.config import settings
from core.personality import get_system_prompt

logger = logging.getLogger("nia.core.brain")

class Brain:
    def __init__(self, model: str, timeout: int):
        self.model_name = model
        self.timeout = timeout
        
        # Load system prompt from personality system (with fallback to settings)
        self.system_prompt = get_system_prompt("default")
        if not self.system_prompt:
            self.system_prompt = settings["brain"].get("system_prompt", "")
        
        # Initialize the LLM for direct conversation
        # Using ChatOllama for streaming chat capabilities
        self.llm = ChatOllama(
            model=self.model_name, 
            temperature=0.7,  # Slightly higher for more natural conversation
            streaming=True,   # Enable streaming for real-time responses
            timeout=self.timeout
        )
        
        logger.info("LangChain ChatOllama initialized with model: %s", self.model_name)
        logger.info("System prompt loaded: %s", self.system_prompt[:50] + "..." if len(self.system_prompt) > 50 else self.system_prompt)

    async def generate_stream(self, prompt: str) -> AsyncGenerator[dict, None]:
        """
        Streams the LLM response token by token for real-time voice interaction.
        Injects personality through system prompts for consistent voice and tone.
        """
        logger.info("Generating streaming response for prompt: '%s'", prompt)
        
        try:
            # Create messages with system prompt for personality injection
            messages = []
            
            # Add system prompt if available for personality
            if self.system_prompt:
                messages.append(SystemMessage(content=self.system_prompt))
            
            # Add user prompt
            messages.append(HumanMessage(content=prompt))
            
            # Stream the response from the LLM
            in_thinking_mode = False
            async for chunk in self.llm.astream(messages):
                if hasattr(chunk, 'content') and chunk.content:
                    content = chunk.content
                    
                    # Check if we're entering thinking mode
                    if '<think>' in content:
                        in_thinking_mode = True
                        # Remove the <think> tag and everything after it in this chunk
                        content = content.split('<think>')[0]
                    
                    # Check if we're exiting thinking mode
                    if '</think>' in content:
                        in_thinking_mode = False
                        # Remove everything before </think> and the tag itself
                        content = content.split('</think>')[-1]
                    
                    # Only yield content if we're not in thinking mode and there's actual content
                    if not in_thinking_mode and content.strip():
                        yield {"response": content, "done": False}
                        logger.debug("Streamed token: %s", content)
            
            # Signal that the stream is complete
            yield {"response": "", "done": True}
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
        return {
            "llm_provider": "Ollama (via LangChain ChatOllama)",
            "configured_model": self.model_name,
            "streaming_enabled": True,
            "personality_loaded": bool(self.system_prompt)
        }

