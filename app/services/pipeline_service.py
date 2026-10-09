"""Pipeline orchestrator for Thai ID Card OCR, Structured LLM Extraction, and Grounding Verification."""

import io
import logging
import time
from typing import Dict, List, Optional
from PIL import Image

from app.clients.ocr_client import AzureOCRClient
from app.models.schemas import (
    OCRDocument,
    OCRWord,
    StageTiming,
    ThaiIdCardData,
    ThaiIdCardExtraction,
    ThaiIdCardLaserData,
    ThaiIdCardLaserExtraction,
    ThaiIdCardLaserResponse,
    ThaiIdCardResponse,
)
from app.services.grounding_service import GroundingService
from app.services.kie_service import KIEService
from app.services.validation_service import ValidationService

logger = logging.getLogger(__name__)


class PipelineService:
    """Orchestrator for ID Card OCR, Structured LLM extraction, Grounding, and Checksum validation."""

    def __init__(
        self,
        ocr_client: Optional[AzureOCRClient] = None,
        kie_service: Optional[KIEService] = None,
        validation_service: Optional[ValidationService] = None,
        grounding_service: Optional[GroundingService] = None,
    ):
        self.ocr_client = ocr_client or AzureOCRClient()
        self.kie_service = kie_service or KIEService()
        self.validation_service = validation_service or ValidationService()
        self.grounding_service = grounding_service or GroundingService()

    def _extract_ocr_doc(self, image_bytes: bytes) -> OCRDocument:
        """Extracts OCRDocument from client or wraps legacy extract_text output."""
        doc = None
        if hasattr(self.ocr_client, "extract_document"):
            try:
                res = self.ocr_client.extract_document(image_bytes)
                if isinstance(res, OCRDocument):
                    doc = res
            except Exception:
                pass

        if doc is None:
            text = self.ocr_client.extract_text(image_bytes)
            if isinstance(text, str):
                words = [OCRWord(content=t, confidence=1.0) for t in text.split() if t.strip()]
                doc = OCRDocument(content=text, words=words)
            else:
                doc = OCRDocument(content="", words=[])
        return doc

    def process_id_card(self, image_bytes: bytes) -> ThaiIdCardResponse:
        """Executes real-time inference (Front): Image Validation -> OCR -> KIE -> Checksum -> Grounding."""
        pipeline_start = time.perf_counter()
        timings_ms: Dict[str, float] = {}

        # Stage 1: Validate image integrity
        t0 = time.perf_counter()
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                img.verify()
        except Exception as exc:
            raise ValueError(f"Invalid or corrupted image payload: {str(exc)}")
        timings_ms["image_validation"] = round((time.perf_counter() - t0) * 1000, 2)

        # Stage 2: Azure Document Intelligence OCR
        t0 = time.perf_counter()
        ocr_doc = self._extract_ocr_doc(image_bytes)
        timings_ms["ocr"] = round((time.perf_counter() - t0) * 1000, 2)

        # Stage 3: LLM Structured Outputs Extraction
        t0 = time.perf_counter()
        extracted: ThaiIdCardExtraction = self.kie_service.extract(ocr_text=ocr_doc.content)
        timings_ms["kie"] = round((time.perf_counter() - t0) * 1000, 2)

        # Stage 4: Checksum Validation & Normalization
        t0 = time.perf_counter()
        is_valid = self.validation_service.validate_thai_id_checksum(extracted.identification_number)
        timings_ms["validation"] = round((time.perf_counter() - t0) * 1000, 2)

        # Stage 5: Grounding & Confidence Scoring
        t0 = time.perf_counter()
        confidence_summary = self.grounding_service.ground_thai_id_card(
            extracted=extracted,
            ocr_doc=ocr_doc,
            is_id_checksum_valid=is_valid,
        )
        timings_ms["grounding"] = round((time.perf_counter() - t0) * 1000, 2)

        total_ms = (time.perf_counter() - pipeline_start) * 1000
        timings_ms["total"] = round(total_ms, 2)

        is_rejected = not confidence_summary.is_quality_gate_passed
        rejection_reason = confidence_summary.rejection_reason

        card_data = ThaiIdCardData(
            **extracted.model_dump(),
            is_id_checksum_valid=is_valid,
            confidence_summary=confidence_summary,
        )

        stages: List[StageTiming] = [
            StageTiming(key="image_validation", label="Image Ingestion & Validation", status="done", ms=timings_ms["image_validation"]),
            StageTiming(key="ocr", label="OCR & Layout Analysis (Azure Document Intelligence)", status="done", ms=timings_ms["ocr"]),
            StageTiming(key="kie", label="LLM Key Information Extraction", status="done", ms=timings_ms["kie"]),
            StageTiming(key="validation", label="13-Digit Checksum & Domain Verification", status="done", ms=timings_ms["validation"]),
            StageTiming(key="grounding", label="OCR Grounding & Quality Gate", status="failed" if is_rejected else "done", ms=timings_ms["grounding"]),
        ]

        return ThaiIdCardResponse(
            status="rejected" if is_rejected else "success",
            is_rejected=is_rejected,
            rejection_reason=rejection_reason,
            data=card_data,
            stages=stages,
            timings_ms=timings_ms,
            processing_time_ms=round(total_ms, 2),
        )

    def process_laser_id(self, image_bytes: bytes) -> ThaiIdCardLaserResponse:
        """Executes real-time inference (Back): Image Validation -> OCR -> KIE -> Format -> Grounding."""
        pipeline_start = time.perf_counter()
        timings_ms: Dict[str, float] = {}

        # Stage 1: Validate image integrity
        t0 = time.perf_counter()
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                img.verify()
        except Exception as exc:
            raise ValueError(f"Invalid or corrupted image payload: {str(exc)}")
        timings_ms["image_validation"] = round((time.perf_counter() - t0) * 1000, 2)

        # Stage 2: Azure Document Intelligence OCR
        t0 = time.perf_counter()
        ocr_doc = self._extract_ocr_doc(image_bytes)
        timings_ms["ocr"] = round((time.perf_counter() - t0) * 1000, 2)

        # Stage 3: LLM Structured Outputs Extraction
        t0 = time.perf_counter()
        extracted: ThaiIdCardLaserExtraction = self.kie_service.extract_laser_id(ocr_text=ocr_doc.content)
        timings_ms["kie"] = round((time.perf_counter() - t0) * 1000, 2)

        # Stage 4: Format Validation & Formatting
        t0 = time.perf_counter()
        target_id = extracted.raw_laser_id or extracted.formatted_laser_id
        is_valid_format = self.validation_service.validate_laser_id_format(target_id)
        formatted_id = extracted.formatted_laser_id or self.validation_service.format_laser_id(extracted.raw_laser_id)
        timings_ms["validation"] = round((time.perf_counter() - t0) * 1000, 2)

        # Stage 5: Grounding & Confidence Scoring
        t0 = time.perf_counter()
        confidence_summary = self.grounding_service.ground_laser_id(
            extracted=extracted,
            ocr_doc=ocr_doc,
            is_laser_id_valid_format=is_valid_format,
        )
        timings_ms["grounding"] = round((time.perf_counter() - t0) * 1000, 2)

        total_ms = (time.perf_counter() - pipeline_start) * 1000
        timings_ms["total"] = round(total_ms, 2)

        is_rejected = not confidence_summary.is_quality_gate_passed
        rejection_reason = confidence_summary.rejection_reason

        card_data = ThaiIdCardLaserData(
            raw_text=extracted.raw_text,
            raw_laser_id=extracted.raw_laser_id,
            formatted_laser_id=formatted_id,
            is_laser_id_valid_format=is_valid_format,
            confidence_summary=confidence_summary,
        )

        stages: List[StageTiming] = [
            StageTiming(key="image_validation", label="Image Ingestion & Validation", status="done", ms=timings_ms["image_validation"]),
            StageTiming(key="ocr", label="OCR & Layout Analysis (Azure Document Intelligence)", status="done", ms=timings_ms["ocr"]),
            StageTiming(key="kie", label="LLM Laser ID Extraction", status="done", ms=timings_ms["kie"]),
            StageTiming(key="validation", label="Laser ID Format Verification", status="done", ms=timings_ms["validation"]),
            StageTiming(key="grounding", label="OCR Grounding & Quality Gate", status="failed" if is_rejected else "done", ms=timings_ms["grounding"]),
        ]

        return ThaiIdCardLaserResponse(
            status="rejected" if is_rejected else "success",
            is_rejected=is_rejected,
            rejection_reason=rejection_reason,
            data=card_data,
            stages=stages,
            timings_ms=timings_ms,
            processing_time_ms=round(total_ms, 2),
        )
