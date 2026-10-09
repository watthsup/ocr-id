"""Real-time ID card OCR & KIE inference endpoints (Front & Laser ID)."""

import base64
import logging
from typing import Optional
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status

from app.core.config import settings
from app.models.schemas import ThaiIdCardLaserResponse, ThaiIdCardResponse
from app.services.pipeline_service import PipelineService

logger = logging.getLogger(__name__)
router = APIRouter()


def get_pipeline_service() -> PipelineService:
    return PipelineService()


async def _extract_image_bytes(request: Request, file: Optional[UploadFile]) -> bytes:
    """Helper to extract and validate image bytes from multipart upload or base64 JSON."""
    image_bytes: bytes = b""

    # 1. Read from uploaded multipart file
    if file is not None:
        image_bytes = await file.read()
    else:
        # 2. Check JSON payload for base64 image
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                body = await request.json()
                raw_b64 = body.get("image_base64", "").strip()
                if "," in raw_b64:
                    raw_b64 = raw_b64.split(",", 1)[1]
                if raw_b64:
                    image_bytes = base64.b64decode(raw_b64)
            except Exception as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid base64 payload: {str(exc)}",
                )

    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An ID card image must be provided as a multipart file or JSON 'image_base64'.",
        )

    # Validate file size
    max_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024
    if len(image_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds size limit of {settings.MAX_IMAGE_SIZE_MB}MB.",
        )

    return image_bytes


@router.post(
    "/id-card",
    response_model=ThaiIdCardResponse,
    summary="Real-Time Thai ID Card OCR & Extraction (Front)",
    description="Accepts an ID card front image file (or JSON with image_base64), runs Azure OCR and LLM extraction, and returns structured data.",
)
async def extract_id_card(
    request: Request,
    file: Optional[UploadFile] = File(None, description="Thai ID card front image file (JPEG, PNG)"),
    strict_quality_gate: bool = False,
    pipeline: PipelineService = Depends(get_pipeline_service),
) -> ThaiIdCardResponse:
    image_bytes = await _extract_image_bytes(request, file)
    try:
        res = pipeline.process_id_card(image_bytes=image_bytes)
        if strict_quality_gate and res.is_rejected:
            raise HTTPException(
                status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
                detail=res.rejection_reason or "Quality gate rejection: overall OCR confidence is below 40%.",
            )
        return res
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Inference error (Front): %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error: {str(exc)}",
        )


@router.post(
    "/laser-id",
    response_model=ThaiIdCardLaserResponse,
    summary="Real-Time Thai ID Card Laser ID Extraction (Back)",
    description="Accepts an ID card back image file (or JSON with image_base64), runs Azure OCR and LLM extraction, and returns structured Laser ID with format validity.",
)
@router.post(
    "/id-card/laser",
    response_model=ThaiIdCardLaserResponse,
    include_in_schema=False,
)
async def extract_laser_id(
    request: Request,
    file: Optional[UploadFile] = File(None, description="Thai ID card back image file (JPEG, PNG)"),
    strict_quality_gate: bool = False,
    pipeline: PipelineService = Depends(get_pipeline_service),
) -> ThaiIdCardLaserResponse:
    image_bytes = await _extract_image_bytes(request, file)
    try:
        res = pipeline.process_laser_id(image_bytes=image_bytes)
        if strict_quality_gate and res.is_rejected:
            raise HTTPException(
                status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
                detail=res.rejection_reason or "Quality gate rejection: overall OCR confidence is below 40%.",
            )
        return res
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Inference error (Laser ID): %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error: {str(exc)}",
        )
