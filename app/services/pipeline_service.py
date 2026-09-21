"""Pipeline orchestrator for Thai ID Card OCR and Structured LLM Extraction."""

import io
import logging
import time
from typing import Optional
from PIL import Image

from app.clients.ocr_client import AzureOCRClient
from app.models.schemas import (
    ThaiIdCardData,
    ThaiIdCardExtraction,
    ThaiIdCardLaserData,
    ThaiIdCardLaserExtraction,
    ThaiIdCardLaserResponse,
    ThaiIdCardResponse,
)
from app.services.kie_service import KIEService
from app.services.validation_service import ValidationService

logger = logging.getLogger(__name__)


class PipelineService:
    """Orchestrator for ID Card OCR, Structured LLM extraction, and checksum/format validation."""

    def __init__(
        self,
        ocr_client: Optional[AzureOCRClient] = None,
        kie_service: Optional[KIEService] = None,
        validation_service: Optional[ValidationService] = None,
    ):
        self.ocr_client = ocr_client or AzureOCRClient()
        self.kie_service = kie_service or KIEService()
        self.validation_service = validation_service or ValidationService()

    def process_id_card(self, image_bytes: bytes) -> ThaiIdCardResponse:
        """Executes real-time inference (Front): OCR -> Structured LLM KIE -> Checksum Verification."""
        start_time = time.perf_counter()

        # Step 0: Validate image integrity
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                img.verify()
        except Exception as exc:
            raise ValueError(f"Invalid or corrupted image payload: {str(exc)}")

        # Step 1: Azure Document Intelligence OCR
        ocr_text = self.ocr_client.extract_text(image_bytes)

        # Step 2: LLM Structured Outputs Extraction (returns validated ThaiIdCardExtraction)
        extracted: ThaiIdCardExtraction = self.kie_service.extract(ocr_text=ocr_text)

        # Step 3: Checksum Validation & Response Assembly
        is_valid = self.validation_service.validate_thai_id_checksum(extracted.identification_number)

        card_data = ThaiIdCardData(
            **extracted.model_dump(),
            is_id_checksum_valid=is_valid,
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return ThaiIdCardResponse(
            status="success",
            data=card_data,
            processing_time_ms=round(elapsed_ms, 2),
        )

    def process_laser_id(self, image_bytes: bytes) -> ThaiIdCardLaserResponse:
        """Executes real-time inference (Back): OCR -> Structured LLM Laser ID -> Format Validation."""
        start_time = time.perf_counter()

        # Step 0: Validate image integrity
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                img.verify()
        except Exception as exc:
            raise ValueError(f"Invalid or corrupted image payload: {str(exc)}")

        # Step 1: Azure Document Intelligence OCR
        ocr_text = self.ocr_client.extract_text(image_bytes)

        # Step 2: LLM Structured Outputs Extraction (returns validated ThaiIdCardLaserExtraction)
        extracted: ThaiIdCardLaserExtraction = self.kie_service.extract_laser_id(ocr_text=ocr_text)

        # Step 3: Format Validation & Formatting
        target_id = extracted.raw_laser_id or extracted.formatted_laser_id
        is_valid_format = self.validation_service.validate_laser_id_format(target_id)
        formatted_id = extracted.formatted_laser_id or self.validation_service.format_laser_id(extracted.raw_laser_id)

        card_data = ThaiIdCardLaserData(
            raw_laser_id=extracted.raw_laser_id,
            formatted_laser_id=formatted_id,
            is_laser_id_valid_format=is_valid_format,
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return ThaiIdCardLaserResponse(
            status="success",
            data=card_data,
            processing_time_ms=round(elapsed_ms, 2),
        )
