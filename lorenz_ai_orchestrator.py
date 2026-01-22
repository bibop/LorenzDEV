#!/usr/bin/env python3
"""
🧠 LORENZ AI Orchestrator
===========================================================

Multi-Model AI System con routing intelligente e capabilities avanzate:
- Claude (Anthropic) - Ragionamento, coding, analisi
- GPT-4 (OpenAI) - General purpose, vision
- Gemini (Google) - Long context, multimodal
- GROQ (Llama) - Ultra-fast inference
- DALL-E (OpenAI) - Image generation
- Perplexity/Tavily - Web search

Autore: Claude Code
Data: 2026-01-14
"""

import os
import json
import logging
import asyncio
import aiohttp
import base64
from typing import Dict, List, Optional, Union, Literal
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# Logging
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class ModelConfig:
    """Configuration for an AI model"""
    name: str
    provider: str
    cost_input: float  # $ per 1M tokens
    cost_output: float
    max_tokens: int
    capabilities: List[str] = field(default_factory=list)
    speed: str = "medium"  # slow, medium, fast, ultra-fast


class TaskType(Enum):
    """Types of tasks for routing"""
    CHAT = "chat"
    CODING = "coding"
    REASONING = "reasoning"
    ANALYSIS = "analysis"
    CREATIVE = "creative"
    VISION = "vision"
    IMAGE_GEN = "image_generation"
    WEB_SEARCH = "web_search"
    LONG_CONTEXT = "long_context"
    FAST_RESPONSE = "fast_response"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"


# Model definitions
MODELS = {
    # Claude models
    "claude-opus": ModelConfig(
        name="claude-3-opus-20240229",
        provider="anthropic",
        cost_input=15.00,
        cost_output=75.00,
        max_tokens=4096,
        capabilities=["reasoning", "coding", "analysis", "creative"],
        speed="slow"
    ),
    "claude-sonnet": ModelConfig(
        name="claude-3-5-sonnet-20241022",
        provider="anthropic",
        cost_input=3.00,
        cost_output=15.00,
        max_tokens=8192,
        capabilities=["reasoning", "coding", "analysis", "creative", "vision"],
        speed="medium"
    ),
    "claude-haiku": ModelConfig(
        name="claude-3-5-haiku-20241022",
        provider="anthropic",
        cost_input=0.25,
        cost_output=1.25,
        max_tokens=4096,
        capabilities=["chat", "fast_response", "summarization"],
        speed="fast"
    ),

    # OpenAI models
    "gpt-4o": ModelConfig(
        name="gpt-4o",
        provider="openai",
        cost_input=2.50,
        cost_output=10.00,
        max_tokens=16384,
        capabilities=["reasoning", "coding", "vision", "creative"],
        speed="medium"
    ),
    "gpt-4o-mini": ModelConfig(
        name="gpt-4o-mini",
        provider="openai",
        cost_input=0.15,
        cost_output=0.60,
        max_tokens=16384,
        capabilities=["chat", "fast_response", "coding"],
        speed="fast"
    ),

    # Google models
    "gemini-pro": ModelConfig(
        name="gemini-1.5-pro",
        provider="google",
        cost_input=1.25,
        cost_output=5.00,
        max_tokens=8192,
        capabilities=["reasoning", "long_context", "vision", "analysis"],
        speed="medium"
    ),
    "gemini-flash": ModelConfig(
        name="gemini-1.5-flash",
        provider="google",
        cost_input=0.075,
        cost_output=0.30,
        max_tokens=8192,
        capabilities=["chat", "fast_response", "long_context"],
        speed="fast"
    ),

    # GROQ models (ultra-fast)
    "groq-llama70b": ModelConfig(
        name="llama-3.1-70b-versatile",
        provider="groq",
        cost_input=0.59,
        cost_output=0.79,
        max_tokens=8192,
        capabilities=["chat", "fast_response", "coding", "reasoning"],
        speed="ultra-fast"
    ),
    "groq-llama8b": ModelConfig(
        name="llama-3.1-8b-instant",
        provider="groq",
        cost_input=0.05,
        cost_output=0.08,
        max_tokens=8192,
        capabilities=["chat", "fast_response"],
        speed="ultra-fast"
    ),
    "groq-mixtral": ModelConfig(
        name="mixtral-8x7b-32768",
        provider="groq",
        cost_input=0.24,
        cost_output=0.24,
        max_tokens=32768,
        capabilities=["chat", "long_context", "coding"],
        speed="ultra-fast"
    ),
}

# Task to model routing
TASK_ROUTING = {
    TaskType.CHAT: ["groq-llama70b", "claude-haiku", "gpt-4o-mini"],
    TaskType.CODING: ["claude-sonnet", "gpt-4o", "groq-llama70b"],
    TaskType.REASONING: ["claude-opus", "claude-sonnet", "gpt-4o"],
    TaskType.ANALYSIS: ["claude-sonnet", "gemini-pro", "gpt-4o"],
    TaskType.CREATIVE: ["claude-sonnet", "gpt-4o", "claude-opus"],
    TaskType.VISION: ["gpt-4o", "claude-sonnet", "gemini-pro"],
    TaskType.LONG_CONTEXT: ["gemini-pro", "groq-mixtral", "claude-sonnet"],
    TaskType.FAST_RESPONSE: ["groq-llama8b", "groq-llama70b", "claude-haiku"],
    TaskType.TRANSLATION: ["gpt-4o", "claude-sonnet", "gemini-pro"],
    TaskType.SUMMARIZATION: ["claude-haiku", "groq-llama70b", "gpt-4o-mini"],
}


# ============================================================================
# AI PROVIDERS
# ============================================================================

class AIProvider:
    """Base class for AI providers"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.enabled = bool(api_key)

    async def complete(self, messages: List[Dict], model: str, **kwargs) -> str:
        raise NotImplementedError


class AnthropicProvider(AIProvider):
    """Anthropic Claude API provider"""

    API_URL = "https://api.anthropic.com/v1/messages"

    async def complete(self, messages: List[Dict], model: str,
                      max_tokens: int = 4096, system: str = None) -> str:
        if not self.enabled:
            raise ValueError("Anthropic API key not configured")

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages
        }

        if system:
            payload["system"] = system

        async with aiohttp.ClientSession() as session:
            async with session.post(self.API_URL, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["content"][0]["text"]
                else:
                    error = await resp.text()
                    raise Exception(f"Anthropic API error {resp.status}: {error}")


class OpenAIProvider(AIProvider):
    """OpenAI API provider"""

    API_URL = "https://api.openai.com/v1/chat/completions"

    async def complete(self, messages: List[Dict], model: str,
                      max_tokens: int = 4096, **kwargs) -> str:
        if not self.enabled:
            raise ValueError("OpenAI API key not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.API_URL, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    error = await resp.text()
                    raise Exception(f"OpenAI API error {resp.status}: {error}")

    async def generate_image(self, prompt: str, size: str = "1024x1024",
                            quality: str = "standard", n: int = 1) -> List[str]:
        """Generate images using DALL-E 3"""
        if not self.enabled:
            raise ValueError("OpenAI API key not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "n": n
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/images/generations",
                headers=headers,
                json=payload
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return [img["url"] for img in data["data"]]
                else:
                    error = await resp.text()
                    raise Exception(f"DALL-E API error {resp.status}: {error}")


class GoogleProvider(AIProvider):
    """Google Gemini API provider"""

    API_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    async def complete(self, messages: List[Dict], model: str,
                      max_tokens: int = 8192, **kwargs) -> str:
        if not self.enabled:
            raise ValueError("Google API key not configured")

        # Convert messages to Gemini format
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })

        url = f"{self.API_URL}/{model}:generateContent?key={self.api_key}"

        payload = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": max_tokens
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    error = await resp.text()
                    raise Exception(f"Gemini API error {resp.status}: {error}")


class GroqProvider(AIProvider):
    """GROQ API provider (ultra-fast inference)"""

    API_URL = "https://api.groq.com/openai/v1/chat/completions"

    async def complete(self, messages: List[Dict], model: str,
                      max_tokens: int = 8192, **kwargs) -> str:
        if not self.enabled:
            raise ValueError("GROQ API key not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.API_URL, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    error = await resp.text()
                    raise Exception(f"GROQ API error {resp.status}: {error}")


class PerplexityProvider(AIProvider):
    """Perplexity API provider (web search)"""

    API_URL = "https://api.perplexity.ai/chat/completions"

    async def search(self, query: str) -> str:
        """Perform web search with Perplexity"""
        if not self.enabled:
            raise ValueError("Perplexity API key not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "llama-3.1-sonar-large-128k-online",
            "messages": [{"role": "user", "content": query}]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.API_URL, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    error = await resp.text()
                    raise Exception(f"Perplexity API error {resp.status}: {error}")


# ============================================================================
# TASK CLASSIFIER
# ============================================================================

class TaskClassifier:
    """Classifies user input to determine best task type"""

    KEYWORDS = {
        TaskType.CODING: ["code", "codice", "programma", "function", "debug", "error",
                         "python", "javascript", "script", "sviluppa", "implementa"],
        TaskType.REASONING: ["perché", "why", "spiega", "explain", "ragiona", "analizza",
                            "confronta", "compare", "valuta", "evaluate"],
        TaskType.CREATIVE: ["scrivi", "write", "crea", "create", "inventa", "storia",
                           "poesia", "poem", "idea", "brainstorm"],
        TaskType.VISION: ["immagine", "image", "foto", "photo", "vedi", "see",
                         "analizza questa", "guarda", "look"],
        TaskType.IMAGE_GEN: ["genera immagine", "crea immagine", "disegna", "draw",
                            "generate image", "make image", "illustra"],
        TaskType.WEB_SEARCH: ["cerca", "search", "trova", "find", "google", "web",
                             "internet", "news", "notizie", "attuale", "current"],
        TaskType.LONG_CONTEXT: ["documento", "document", "file", "pdf", "libro", "book",
                               "lungo", "long", "intero", "entire"],
        TaskType.FAST_RESPONSE: ["veloce", "fast", "quick", "subito", "immediately",
                                "breve", "short", "semplice", "simple"],
        TaskType.TRANSLATION: ["traduci", "translate", "traduzione", "translation",
                              "in inglese", "in italiano", "language"],
        TaskType.SUMMARIZATION: ["riassumi", "summarize", "sintesi", "summary",
                                "punti chiave", "key points", "tldr"],
    }

    @classmethod
    def classify(cls, text: str) -> TaskType:
        """Classify text into task type"""
        text_lower = text.lower()

        # Check for keywords
        scores = {task: 0 for task in TaskType}

        for task_type, keywords in cls.KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    scores[task_type] += 1

        # Find highest scoring task
        max_score = max(scores.values())
        if max_score > 0:
            for task_type, score in scores.items():
                if score == max_score:
                    return task_type

        # Default to chat
        return TaskType.CHAT

    @classmethod
    def should_use_web_search(cls, text: str) -> bool:
        """Determine if query needs web search"""
        indicators = [
            "oggi", "today", "attuale", "current", "recente", "recent",
            "ultimo", "latest", "2024", "2025", "2026",
            "news", "notizie", "prezzo", "price", "borsa", "stock"
        ]
        text_lower = text.lower()
        return any(ind in text_lower for ind in indicators)


# ============================================================================
# AI ORCHESTRATOR
# ============================================================================

class AIOrchestrator:
    """
    Main AI Orchestrator - routes tasks to best model/provider
    """

    def __init__(self):
        # Load API keys from environment
        self.providers = {
            "anthropic": AnthropicProvider(os.getenv("CLAUDE_API_KEY", "")),
            "openai": OpenAIProvider(os.getenv("OPENAI_API_KEY", "")),
            "google": GoogleProvider(os.getenv("GEMINI_API_KEY", "")),
            "groq": GroqProvider(os.getenv("GROQ_API_KEY", "")),
            "perplexity": PerplexityProvider(os.getenv("PERPLEXITY_API_KEY", "")),
        }

        # Stats tracking
        self.stats = {
            "total_requests": 0,
            "by_provider": {},
            "by_task": {},
            "errors": 0
        }

        logger.info("🧠 AI Orchestrator initialized")
        self._log_available_providers()

    def _log_available_providers(self):
        """Log which providers are available"""
        for name, provider in self.providers.items():
            status = "✅" if provider.enabled else "❌"
            logger.info(f"  {status} {name.upper()}")

    def has_available_provider(self) -> bool:
        """Check if at least one provider is available"""
        return any(p.enabled for p in self.providers.values())

    def get_available_models(self) -> List[str]:
        """Get list of available models based on configured API keys"""
        available = []
        for model_key, config in MODELS.items():
            provider = self.providers.get(config.provider)
            if provider and provider.enabled:
                available.append(model_key)
        return available

    def _select_model(self, task_type: TaskType, prefer_fast: bool = False,
                     prefer_cheap: bool = False) -> Optional[str]:
        """Select best available model for task"""
        candidates = TASK_ROUTING.get(task_type, TASK_ROUTING[TaskType.CHAT])

        for model_key in candidates:
            config = MODELS.get(model_key)
            if not config:
                continue

            provider = self.providers.get(config.provider)
            if provider and provider.enabled:
                # Check preferences
                if prefer_fast and config.speed not in ["fast", "ultra-fast"]:
                    continue
                if prefer_cheap and config.cost_input > 1.0:
                    continue
                return model_key

        # Fallback: any available model
        for model_key in self.get_available_models():
            return model_key

        return None

    async def process(self,
                     prompt: str,
                     task_type: TaskType = None,
                     model: str = None,
                     context: str = None,
                     system_prompt: str = None,
                     prefer_fast: bool = False,
                     prefer_cheap: bool = False,
                     images: List[str] = None) -> Dict:
        """
        Process a request through the orchestrator

        Args:
            prompt: User prompt
            task_type: Force task type (or auto-classify)
            model: Force specific model
            context: Additional context
            system_prompt: System prompt
            prefer_fast: Prefer faster models
            prefer_cheap: Prefer cheaper models
            images: List of image URLs/base64 for vision tasks

        Returns:
            Dict with response, model used, stats
        """
        start_time = datetime.now()

        # Auto-classify if no task type specified
        if task_type is None:
            task_type = TaskClassifier.classify(prompt)

        # Check if web search is needed
        needs_search = TaskClassifier.should_use_web_search(prompt)
        if needs_search and task_type == TaskType.CHAT:
            task_type = TaskType.WEB_SEARCH

        # Select model if not specified
        if model is None:
            model = self._select_model(task_type, prefer_fast, prefer_cheap)

        if model is None:
            return {
                "success": False,
                "error": "No AI models available. Check API keys.",
                "response": None
            }

        model_config = MODELS[model]
        provider = self.providers[model_config.provider]

        # Build messages
        messages = []

        if context:
            messages.append({
                "role": "user",
                "content": f"Context:\n{context}\n\n---\n\n{prompt}"
            })
        else:
            messages.append({
                "role": "user",
                "content": prompt
            })

        # Handle web search
        if task_type == TaskType.WEB_SEARCH:
            perplexity = self.providers.get("perplexity")
            if perplexity and perplexity.enabled:
                try:
                    response = await perplexity.search(prompt)
                    return {
                        "success": True,
                        "response": response,
                        "model": "perplexity-sonar",
                        "provider": "perplexity",
                        "task_type": task_type.value,
                        "duration_ms": (datetime.now() - start_time).total_seconds() * 1000
                    }
                except Exception as e:
                    logger.error(f"Perplexity search failed: {e}")
                    # Fall through to regular model

        # Execute request
        try:
            response = await provider.complete(
                messages=messages,
                model=model_config.name,
                max_tokens=model_config.max_tokens,
                system=system_prompt
            )

            # Update stats
            self.stats["total_requests"] += 1
            self.stats["by_provider"][model_config.provider] = \
                self.stats["by_provider"].get(model_config.provider, 0) + 1
            self.stats["by_task"][task_type.value] = \
                self.stats["by_task"].get(task_type.value, 0) + 1

            duration = (datetime.now() - start_time).total_seconds() * 1000

            return {
                "success": True,
                "response": response,
                "model": model,
                "provider": model_config.provider,
                "task_type": task_type.value,
                "duration_ms": duration
            }

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"AI request failed: {e}")

            return {
                "success": False,
                "error": str(e),
                "response": None,
                "model": model
            }

    async def generate_image(self, prompt: str,
                            size: str = "1024x1024",
                            quality: str = "standard") -> Dict:
        """Generate an image using DALL-E"""
        openai = self.providers.get("openai")

        if not openai or not openai.enabled:
            return {
                "success": False,
                "error": "OpenAI API key not configured for image generation"
            }

        try:
            urls = await openai.generate_image(prompt, size, quality)
            return {
                "success": True,
                "urls": urls,
                "prompt": prompt
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def web_search(self, query: str) -> Dict:
        """Perform a web search"""
        perplexity = self.providers.get("perplexity")

        if not perplexity or not perplexity.enabled:
            # Fallback: use a regular model with search instruction
            return await self.process(
                prompt=f"Search the web and provide current information about: {query}",
                task_type=TaskType.CHAT,
                system_prompt="You are a helpful assistant. Note: You don't have access to real-time web data. Provide the best answer you can based on your training data, and indicate when information might be outdated."
            )

        try:
            response = await perplexity.search(query)
            return {
                "success": True,
                "response": response,
                "source": "perplexity"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_stats(self) -> Dict:
        """Get orchestrator statistics"""
        return {
            **self.stats,
            "available_models": self.get_available_models(),
            "providers": {
                name: provider.enabled
                for name, provider in self.providers.items()
            }
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Global orchestrator instance
_orchestrator: Optional[AIOrchestrator] = None

def get_orchestrator() -> AIOrchestrator:
    """Get or create the global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AIOrchestrator()
    return _orchestrator


async def ask(prompt: str, **kwargs) -> str:
    """Quick ask function"""
    orchestrator = get_orchestrator()
    result = await orchestrator.process(prompt, **kwargs)
    if result["success"]:
        return result["response"]
    else:
        return f"❌ Error: {result.get('error', 'Unknown error')}"


async def generate_image(prompt: str, **kwargs) -> Dict:
    """Quick image generation function"""
    orchestrator = get_orchestrator()
    return await orchestrator.generate_image(prompt, **kwargs)


async def search(query: str) -> str:
    """Quick web search function"""
    orchestrator = get_orchestrator()
    result = await orchestrator.web_search(query)
    if result["success"]:
        return result["response"]
    else:
        return f"❌ Search error: {result.get('error', 'Unknown error')}"


# ============================================================================
# CLI TEST
# ============================================================================

if __name__ == "__main__":
    import sys

    async def test():
        orchestrator = AIOrchestrator()

        print("\n🧠 LORENZ AI Orchestrator Test")
        print("=" * 50)

        # Show available models
        models = orchestrator.get_available_models()
        print(f"\n✅ Available models: {models}")

        # Test classification
        test_prompts = [
            "Scrivi una funzione Python per calcolare il fattoriale",
            "Cerca le ultime notizie su Apple",
            "Genera un'immagine di un gatto nello spazio",
            "Ciao, come stai?",
            "Riassumi questo documento...",
        ]

        print("\n📋 Task Classification Test:")
        for prompt in test_prompts:
            task = TaskClassifier.classify(prompt)
            print(f"  '{prompt[:40]}...' → {task.value}")

        # Test actual request if API key available
        if models:
            print("\n🚀 Testing API request...")
            result = await orchestrator.process(
                "Dimmi una curiosità interessante in una frase.",
                prefer_fast=True
            )
            if result["success"]:
                print(f"  Model: {result['model']}")
                print(f"  Response: {result['response'][:200]}...")
                print(f"  Duration: {result['duration_ms']:.0f}ms")
            else:
                print(f"  ❌ Error: {result['error']}")

        print("\n📊 Stats:", orchestrator.get_stats())

    asyncio.run(test())
