from typing import List, Dict, Any, Optional, Tuple
import os
from openai import AsyncOpenAI
from .base import AIProvider

class OpenRouterProvider(AIProvider):
    """
    OpenRouter provider implementation.
    Allows access to Kimi k2.5, DeepSeek, and other models.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is not set")
            
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )
        
        # Default model mapping
        self.default_model = "moonshotai/kimi-k2.5" # Latest Kimi

    @property
    def enabled(self) -> bool:
        """Check if provider is enabled (has API key)"""
        return bool(self.api_key) and "placeholder" not in self.api_key

    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system: Optional[str] = None,
        **kwargs
    ) -> Tuple[str, int, int]:
        target_model = model or self.default_model
        
        # Handle system prompt
        final_messages = messages.copy()
        if system:
            final_messages.insert(0, {"role": "system", "content": system})
            
        response = await self.client.chat.completions.create(
            model=target_model,
            messages=final_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_headers={
                "HTTP-Referer": "https://lorenz.bibop.com",
                "X-Title": "LORENZ AI Platform",
            },
            **kwargs
        )
        
        text = response.choices[0].message.content
        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        
        return text, input_tokens, output_tokens

    async def stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system: Optional[str] = None,
        **kwargs
    ):
        target_model = model or self.default_model
        
        # Handle system prompt
        final_messages = messages.copy()
        if system:
            final_messages.insert(0, {"role": "system", "content": system})
            
        stream = await self.client.chat.completions.create(
            model=target_model,
            messages=final_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            extra_headers={
                "HTTP-Referer": "https://lorenz.bibop.com",
                "X-Title": "LORENZ AI Platform",
            },
            **kwargs
        )
        
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content
