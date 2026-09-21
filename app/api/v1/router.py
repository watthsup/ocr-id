"""API v1 router configuration."""

from fastapi import APIRouter
from app.api.v1.endpoints import id_card

api_router = APIRouter()
api_router.include_router(id_card.router, prefix="/ocr", tags=["Thai ID Card OCR & KIE"])
