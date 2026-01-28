"""
LORENZ SaaS - Main FastAPI Application
Multi-tenant AI Personal Assistant Platform
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time

from app.config import settings
from app.database import init_db, close_db

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    await init_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    await close_db()
    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="LORENZ - The World's Most Advanced Human Digital Twin System",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:3000",
        "http://localhost:3001",
        "https://bibop.com",
        "https://www.bibop.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header to all responses"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else "Disabled in production",
    }


# Import and include routers
from app.api.v1 import auth, users, email, chat, rag, onboarding, skills, knowledge, execution, twin, social_graph, rsi, voice_avatar, voice_providers, voices, voice_stream, tts

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(email.router, prefix="/api/v1/email", tags=["Email"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(rag.router, prefix="/api/v1/rag", tags=["RAG"])
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["MNEME Knowledge Base"])
app.include_router(skills.router, prefix="/api/v1/skills", tags=["Skills"])
app.include_router(onboarding.router, prefix="/api/v1/onboarding", tags=["Onboarding"])
app.include_router(execution.router, prefix="/api/v1/exec", tags=["Execution"])
app.include_router(twin.router, prefix="/api/v1/twin", tags=["Human Digital Twin"])
app.include_router(social_graph.router, prefix="/api/v1", tags=["Social Graph"])
app.include_router(rsi.router, prefix="/api/v1", tags=["RSI"])
app.include_router(voice_avatar.router, prefix="/api/v1/twin", tags=["Voice & Avatar"])
app.include_router(voice_providers.router, prefix="/api/v1/voice", tags=["Voice Providers"])
app.include_router(voices.router, prefix="/api/v1/voice", tags=["Voice Management"])
app.include_router(voice_stream.router, prefix="/api/v1", tags=["Voice Streaming"])
app.include_router(tts.router, prefix="/api/v1", tags=["TTS"])

# Webhook routers
from app.api.webhooks import telegram as telegram_webhook

app.include_router(telegram_webhook.router, prefix="/webhooks", tags=["Webhooks"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
