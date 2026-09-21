"""FastAPI main application entrypoint."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up %s (env: %s)...", settings.APP_NAME, settings.APP_ENV)
    logger.info("OCR Engine: Azure Document Intelligence (%s)", settings.AZURE_DOCUMENT_INTELLIGENCE_MODEL_ID)
    logger.info("Default LLM Provider: %s", settings.LLM_PROVIDER)
    yield
    logger.info("Shutting down %s...", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    description="Real-time Thai National ID Card OCR and Key Information Extraction (KIE) Service powered by Azure Document Intelligence and LLMs (OpenAI & Azure AI Foundry).",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
async def health_check():
    """Service health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "ocr_engine": "azure_document_intelligence",
        "default_llm_provider": settings.LLM_PROVIDER,
    }


# Mount API V1 routes
app.include_router(api_router, prefix="/api/v1")
