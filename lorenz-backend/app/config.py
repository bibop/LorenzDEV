"""
LORENZ SaaS - Configuration Settings
Multi-tenant AI Personal Assistant Platform
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # App Info
    APP_NAME: str = "LORENZ"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True  # Set to True for voice testing

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://lorenz:lorenz@localhost:5432/lorenz"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Qdrant Vector DB
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: Optional[str] = None

    # Security
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ENCRYPTION_KEY: str = "change-me-use-fernet-key"  # For encrypting OAuth tokens

    # OAuth - Google
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/oauth/google/callback"

    # OAuth - Microsoft
    MICROSOFT_CLIENT_ID: Optional[str] = None
    MICROSOFT_CLIENT_SECRET: Optional[str] = None
    MICROSOFT_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/oauth/microsoft/callback"
    MICROSOFT_TENANT_ID: str = "common"

    # OAuth - LinkedIn
    LINKEDIN_CLIENT_ID: Optional[str] = None
    LINKEDIN_CLIENT_SECRET: Optional[str] = None
    LINKEDIN_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/oauth/linkedin/callback"

    # OAuth - Twitter/X
    TWITTER_CLIENT_ID: Optional[str] = None
    TWITTER_CLIENT_SECRET: Optional[str] = None
    TWITTER_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/oauth/twitter/callback"

    # OAuth - Meta (Facebook/Instagram)
    META_APP_ID: Optional[str] = None
    META_APP_SECRET: Optional[str] = None
    META_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/oauth/meta/callback"

    # AI Providers
    CLAUDE_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    PERPLEXITY_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    ELEVENLABS_API_KEY: Optional[str] = None
    
    # Voice Providers
    PERSONAPLEX_URL: str = "http://localhost:8080"

    # RAG Configuration
    RAG_EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    RAG_RERANKER_MODEL: str = "BAAI/bge-reranker-base"
    RAG_DEFAULT_TOP_K: int = 5

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_WEBHOOK_URL: Optional[str] = None

    # Email (Default/Fallback IMAP server)
    DEFAULT_IMAP_HOST: str = "mail.hyperloopitalia.com"
    DEFAULT_SMTP_HOST: str = "mail.hyperloopitalia.com"
    DEFAULT_IMAP_PORT: int = 993
    DEFAULT_SMTP_PORT: int = 587

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # File Storage (S3-compatible)
    S3_ENDPOINT: Optional[str] = None  # None for AWS S3, set for MinIO
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_BUCKET_NAME: str = "lorenz-files"
    S3_REGION: str = "us-east-1"

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds

    # Stripe Billing
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_PRICE_ID_PRO: Optional[str] = None
    STRIPE_PRICE_ID_BUSINESS: Optional[str] = None

    # Apify (for Social Graph scraping)
    APIFY_API_KEY: Optional[str] = None
    APIFY_WHATSAPP_ACTOR_ID: str = "extremescrapes~whatsapp-messages-scraper"
    APIFY_LINKEDIN_ACTOR_ID: str = "curious_coder~linkedin-profile-scraper"
    APIFY_LINKEDIN_BULK_ACTOR_ID: str = "bebity~linkedin-premium-actor"

    # Frontend URL (for CORS and redirects)
    FRONTEND_URL: str = "http://localhost:3000"

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
