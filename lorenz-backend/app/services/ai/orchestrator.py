"""
LORENZ SaaS - AI Orchestrator Integration
==========================================

Multi-model AI routing adapted from lorenz_ai_orchestrator.py
for multi-tenant SaaS deployment.

Features:
- Multi-provider support: Claude, GPT-4, Gemini, GROQ, Perplexity
- Task-based routing for cost optimization
- Per-tenant API key management
- Usage tracking and billing integration
"""

import os
import logging
import aiohttp
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from uuid import UUID

from app.config import settings

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
    """Types of tasks for intelligent routing"""
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
    EMAIL_DRAFT = "email_draft"
    CALENDAR = "calendar"


# Model definitions with current pricing (2026)
# Note: Models are detected dynamically at startup
MODELS = {
    # Claude models (Anthropic) - Updated for 2026
    "claude-sonnet": ModelConfig(
        name="claude-sonnet-4-20250514",  # Claude Sonnet 4 - available
        provider="anthropic",
        cost_input=3.00,
        cost_output=15.00,
        max_tokens=8192,
        capabilities=["reasoning", "coding", "analysis", "creative", "vision"],
        speed="medium"
    ),
    "claude-haiku": ModelConfig(
        name="claude-3-5-haiku-20241022",  # Claude 3.5 Haiku - available
        provider="anthropic",
        cost_input=0.25,
        cost_output=1.25,
        max_tokens=4096,
        capabilities=["chat", "fast_response", "summarization", "coding"],
        speed="fast"
    ),
    "claude-haiku-latest": ModelConfig(
        name="claude-3-5-haiku-latest",  # Latest Haiku - available
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

    # Google Gemini models
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

    # GROQ models (ultra-fast inference)
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

# Task to model routing preferences
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
    TaskType.EMAIL_DRAFT: ["claude-sonnet", "gpt-4o", "gemini-pro"],
    TaskType.CALENDAR: ["claude-haiku", "gpt-4o-mini", "groq-llama8b"],
}


# ============================================================================
# AI PROVIDERS
# ============================================================================

class AIProvider:
    """Base class for AI providers"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.enabled = bool(api_key)

    async def complete(
        self,
        messages: List[Dict],
        model: str,
        **kwargs
    ) -> Tuple[str, int, int]:
        """
        Complete a chat request

        Returns:
            Tuple of (response_text, input_tokens, output_tokens)
        """
        raise NotImplementedError


class AnthropicProvider(AIProvider):
    """Anthropic Claude API provider"""

    API_URL = "https://api.anthropic.com/v1/messages"

    async def complete(
        self,
        messages: List[Dict],
        model: str,
        max_tokens: int = 4096,
        system: str = None
    ) -> Tuple[str, int, int]:
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
                data = await resp.json()

                if resp.status != 200:
                    raise Exception(f"Anthropic API error {resp.status}: {data}")

                text = data["content"][0]["text"]
                usage = data.get("usage", {})
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)

                return text, input_tokens, output_tokens


class OpenAIProvider(AIProvider):
    """OpenAI API provider"""

    API_URL = "https://api.openai.com/v1/chat/completions"

    async def complete(
        self,
        messages: List[Dict],
        model: str,
        max_tokens: int = 4096,
        **kwargs
    ) -> Tuple[str, int, int]:
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
                data = await resp.json()

                if resp.status != 200:
                    raise Exception(f"OpenAI API error {resp.status}: {data}")

                text = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)

                return text, input_tokens, output_tokens

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        n: int = 1
    ) -> List[str]:
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
                data = await resp.json()

                if resp.status != 200:
                    raise Exception(f"DALL-E API error {resp.status}: {data}")

                return [img["url"] for img in data["data"]]


class GoogleProvider(AIProvider):
    """Google Gemini API provider"""

    API_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    async def complete(
        self,
        messages: List[Dict],
        model: str,
        max_tokens: int = 8192,
        **kwargs
    ) -> Tuple[str, int, int]:
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
                data = await resp.json()

                if resp.status != 200:
                    raise Exception(f"Gemini API error {resp.status}: {data}")

                text = data["candidates"][0]["content"]["parts"][0]["text"]
                # Gemini doesn't return detailed token counts in the same way
                usage = data.get("usageMetadata", {})
                input_tokens = usage.get("promptTokenCount", 0)
                output_tokens = usage.get("candidatesTokenCount", 0)

                return text, input_tokens, output_tokens


class GroqProvider(AIProvider):
    """GROQ API provider (ultra-fast inference)"""

    API_URL = "https://api.groq.com/openai/v1/chat/completions"

    async def complete(
        self,
        messages: List[Dict],
        model: str,
        max_tokens: int = 8192,
        **kwargs
    ) -> Tuple[str, int, int]:
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
                data = await resp.json()

                if resp.status != 200:
                    raise Exception(f"GROQ API error {resp.status}: {data}")

                text = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)

                return text, input_tokens, output_tokens


class PerplexityProvider(AIProvider):
    """Perplexity API provider (web search)"""

    API_URL = "https://api.perplexity.ai/chat/completions"

    async def search(self, query: str) -> Tuple[str, List[str]]:
        """
        Perform web search with Perplexity

        Returns:
            Tuple of (response_text, citations)
        """
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
                data = await resp.json()

                if resp.status != 200:
                    raise Exception(f"Perplexity API error {resp.status}: {data}")

                text = data["choices"][0]["message"]["content"]
                citations = data.get("citations", [])

                return text, citations


# ============================================================================
# TASK CLASSIFIER
# ============================================================================

class TaskClassifier:
    """Classifies user input to determine best task type"""

    KEYWORDS = {
        TaskType.CODING: [
            "code", "codice", "programma", "function", "debug", "error",
            "python", "javascript", "script", "sviluppa", "implementa",
            "bug", "fix", "refactor"
        ],
        TaskType.REASONING: [
            "perché", "why", "spiega", "explain", "ragiona", "analizza",
            "confronta", "compare", "valuta", "evaluate", "reason"
        ],
        TaskType.CREATIVE: [
            "scrivi", "write", "crea", "create", "inventa", "storia",
            "poesia", "poem", "idea", "brainstorm", "marketing"
        ],
        TaskType.VISION: [
            "immagine", "image", "foto", "photo", "vedi", "see",
            "analizza questa", "guarda", "look", "screenshot"
        ],
        TaskType.IMAGE_GEN: [
            "genera immagine", "crea immagine", "disegna", "draw",
            "generate image", "make image", "illustra", "dall-e"
        ],
        TaskType.WEB_SEARCH: [
            "cerca", "search", "trova", "find", "google", "web",
            "internet", "news", "notizie", "attuale", "current"
        ],
        TaskType.LONG_CONTEXT: [
            "documento", "document", "file", "pdf", "libro", "book",
            "lungo", "long", "intero", "entire", "all"
        ],
        TaskType.FAST_RESPONSE: [
            "veloce", "fast", "quick", "subito", "immediately",
            "breve", "short", "semplice", "simple"
        ],
        TaskType.TRANSLATION: [
            "traduci", "translate", "traduzione", "translation",
            "in inglese", "in italiano", "language"
        ],
        TaskType.SUMMARIZATION: [
            "riassumi", "summarize", "sintesi", "summary",
            "punti chiave", "key points", "tldr"
        ],
        TaskType.EMAIL_DRAFT: [
            "email", "mail", "scrivi email", "rispondi", "reply",
            "draft", "bozza", "messaggio"
        ],
        TaskType.CALENDAR: [
            "calendario", "calendar", "appuntamento", "meeting",
            "schedule", "evento", "event", "reminder"
        ],
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

class SaaSAIOrchestrator:
    """
    Multi-tenant AI Orchestrator for SaaS deployment

    Features:
    - Multi-provider routing (Claude, GPT-4, Gemini, GROQ)
    - Task-based model selection
    - Per-tenant usage tracking
    - Cost optimization
    """

    def __init__(
        self,
        tenant_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        custom_api_keys: Optional[Dict[str, str]] = None
    ):
        self.tenant_id = tenant_id
        self.user_id = user_id

        # Use custom API keys if provided, otherwise use platform defaults
        api_keys = custom_api_keys or {}

        self.providers = {
            "anthropic": AnthropicProvider(
                api_keys.get("CLAUDE_API_KEY", settings.CLAUDE_API_KEY or "")
            ),
            "openai": OpenAIProvider(
                api_keys.get("OPENAI_API_KEY", settings.OPENAI_API_KEY or "")
            ),
            "google": GoogleProvider(
                api_keys.get("GEMINI_API_KEY", settings.GEMINI_API_KEY or "")
            ),
            "groq": GroqProvider(
                api_keys.get("GROQ_API_KEY", settings.GROQ_API_KEY or "")
            ),
            "perplexity": PerplexityProvider(
                api_keys.get("PERPLEXITY_API_KEY", settings.PERPLEXITY_API_KEY or "")
            ),
        }

        # Stats tracking
        self.session_stats = {
            "total_requests": 0,
            "by_provider": {},
            "by_task": {},
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "errors": 0
        }

        logger.info(f"AI Orchestrator initialized for tenant {tenant_id}")
        self._log_available_providers()

    def _log_available_providers(self):
        """Log which providers are available"""
        for name, provider in self.providers.items():
            status = "enabled" if provider.enabled else "disabled"
            logger.debug(f"  Provider {name}: {status}")

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

    def _select_model(
        self,
        task_type: TaskType,
        prefer_fast: bool = False,
        prefer_cheap: bool = False,
        required_capabilities: Optional[List[str]] = None
    ) -> Optional[str]:
        """Select best available model for task"""
        candidates = TASK_ROUTING.get(task_type, TASK_ROUTING[TaskType.CHAT])

        for model_key in candidates:
            config = MODELS.get(model_key)
            if not config:
                continue

            provider = self.providers.get(config.provider)
            if not provider or not provider.enabled:
                continue

            # Check preferences
            if prefer_fast and config.speed not in ["fast", "ultra-fast"]:
                continue
            if prefer_cheap and config.cost_input > 1.0:
                continue

            # Check required capabilities
            if required_capabilities:
                if not all(cap in config.capabilities for cap in required_capabilities):
                    continue

            return model_key

        # Fallback: any available model
        for model_key in self.get_available_models():
            return model_key

        return None

    def _calculate_cost(
        self,
        model_key: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Calculate cost in USD"""
        config = MODELS.get(model_key)
        if not config:
            return 0.0

        input_cost = (input_tokens / 1_000_000) * config.cost_input
        output_cost = (output_tokens / 1_000_000) * config.cost_output

        return input_cost + output_cost

    async def process(
        self,
        prompt: str,
        task_type: TaskType = None,
        model: str = None,
        context: str = None,
        system_prompt: str = None,
        conversation_history: List[Dict] = None,
        prefer_fast: bool = False,
        prefer_cheap: bool = False,
        images: List[str] = None,
        max_tokens: int = None
    ) -> Dict:
        """
        Process a request through the orchestrator

        Args:
            prompt: User prompt
            task_type: Force task type (or auto-classify)
            model: Force specific model
            context: Additional context (RAG results, etc.)
            system_prompt: System prompt
            conversation_history: Previous messages
            prefer_fast: Prefer faster models
            prefer_cheap: Prefer cheaper models
            images: List of image URLs/base64 for vision tasks
            max_tokens: Override max tokens

        Returns:
            Dict with response, model used, stats, cost
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
                "response": None,
                "model": None,
                "task_type": task_type.value if task_type else None
            }

        model_config = MODELS[model]
        provider = self.providers[model_config.provider]

        # Build messages
        messages = []

        if conversation_history:
            messages.extend(conversation_history)

        # Add context if provided
        if context:
            user_content = f"Context:\n{context}\n\n---\n\n{prompt}"
        else:
            user_content = prompt

        messages.append({
            "role": "user",
            "content": user_content
        })

        # Handle web search separately
        if task_type == TaskType.WEB_SEARCH:
            perplexity = self.providers.get("perplexity")
            if perplexity and perplexity.enabled:
                try:
                    response, citations = await perplexity.search(prompt)
                    duration = (datetime.now() - start_time).total_seconds() * 1000

                    return {
                        "success": True,
                        "response": response,
                        "model": "perplexity-sonar",
                        "provider": "perplexity",
                        "task_type": task_type.value,
                        "duration_ms": duration,
                        "citations": citations,
                        "tokens": {"input": 0, "output": 0},
                        "cost_usd": 0.005  # Flat rate estimate for Perplexity
                    }
                except Exception as e:
                    logger.error(f"Perplexity search failed: {e}")
                    # Fall through to regular model

        # Execute request
        try:
            tokens_limit = max_tokens or model_config.max_tokens

            response, input_tokens, output_tokens = await provider.complete(
                messages=messages,
                model=model_config.name,
                max_tokens=tokens_limit,
                system=system_prompt
            )

            # Calculate cost
            cost = self._calculate_cost(model, input_tokens, output_tokens)

            # Update session stats
            self.session_stats["total_requests"] += 1
            self.session_stats["by_provider"][model_config.provider] = \
                self.session_stats["by_provider"].get(model_config.provider, 0) + 1
            self.session_stats["by_task"][task_type.value] = \
                self.session_stats["by_task"].get(task_type.value, 0) + 1
            self.session_stats["total_tokens"] += input_tokens + output_tokens
            self.session_stats["total_cost_usd"] += cost

            duration = (datetime.now() - start_time).total_seconds() * 1000

            return {
                "success": True,
                "response": response,
                "model": model,
                "provider": model_config.provider,
                "task_type": task_type.value,
                "duration_ms": duration,
                "tokens": {
                    "input": input_tokens,
                    "output": output_tokens,
                    "total": input_tokens + output_tokens
                },
                "cost_usd": cost
            }

        except Exception as e:
            self.session_stats["errors"] += 1
            logger.error(f"AI request failed: {e}")

            return {
                "success": False,
                "error": str(e),
                "response": None,
                "model": model,
                "task_type": task_type.value if task_type else None
            }

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard"
    ) -> Dict:
        """Generate an image using DALL-E"""
        openai = self.providers.get("openai")

        if not openai or not openai.enabled:
            return {
                "success": False,
                "error": "OpenAI API key not configured for image generation"
            }

        try:
            urls = await openai.generate_image(prompt, size, quality)

            # Estimate cost (DALL-E 3 pricing)
            cost = 0.04 if quality == "standard" else 0.08
            if size != "1024x1024":
                cost *= 1.5

            return {
                "success": True,
                "urls": urls,
                "prompt": prompt,
                "cost_usd": cost
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
            response, citations = await perplexity.search(query)
            return {
                "success": True,
                "response": response,
                "citations": citations,
                "source": "perplexity"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_session_stats(self) -> Dict:
        """Get session statistics"""
        return {
            **self.session_stats,
            "available_models": self.get_available_models(),
            "providers": {
                name: provider.enabled
                for name, provider in self.providers.items()
            }
        }


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_orchestrator(
    tenant_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    custom_api_keys: Optional[Dict[str, str]] = None
) -> SaaSAIOrchestrator:
    """
    Factory function to create an AI orchestrator instance

    Args:
        tenant_id: Tenant UUID for multi-tenant tracking
        user_id: User UUID for usage tracking
        custom_api_keys: Optional custom API keys (for BYOK - Bring Your Own Key)

    Returns:
        Configured SaaSAIOrchestrator instance
    """
    return SaaSAIOrchestrator(
        tenant_id=tenant_id,
        user_id=user_id,
        custom_api_keys=custom_api_keys
    )
