"""Outbound client for Azure Document Intelligence OCR service with full metadata extraction."""

import logging
from typing import List, Optional
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

from app.core.config import settings
from app.models.schemas import OCRDocument, OCRLine, OCRWord

logger = logging.getLogger(__name__)


class AzureOCRClient:
    """Outbound adapter wrapping Azure Document Intelligence SDK."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        key: Optional[str] = None,
        model_id: Optional[str] = None,
    ):
        self.endpoint = endpoint or settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT
        self.key = key or settings.AZURE_DOCUMENT_INTELLIGENCE_KEY
        self.model_id = model_id or settings.AZURE_DOCUMENT_INTELLIGENCE_MODEL_ID
        self._client: Optional[DocumentIntelligenceClient] = None

    def _get_client(self) -> DocumentIntelligenceClient:
        if self._client is None:
            self._client = DocumentIntelligenceClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.key),
            )
        return self._client

    def extract_document(self, image_bytes: bytes) -> OCRDocument:
        """Sends image bytes to Azure Document Intelligence and returns structured OCR document

        with word-level confidence scores, bounding polygons, and full text content.
        """
        client = self._get_client()
        logger.info("Calling Azure Document Intelligence (model: %s)", self.model_id)

        poller = client.begin_analyze_document(
            model_id=self.model_id,
            body=image_bytes,
            content_type="application/octet-stream",
        )
        result = poller.result()

        raw_content = result.content or ""
        words: List[OCRWord] = []
        lines: List[OCRLine] = []
        page_width: Optional[float] = None
        page_height: Optional[float] = None
        page_unit: Optional[str] = None

        if hasattr(result, "pages") and result.pages:
            for page in result.pages:
                if page_width is None and hasattr(page, "width"):
                    page_width = float(page.width) if page.width is not None else None
                if page_height is None and hasattr(page, "height"):
                    page_height = float(page.height) if page.height is not None else None
                if page_unit is None and hasattr(page, "unit"):
                    page_unit = str(page.unit) if page.unit else None

                # Extract word-level tokens with confidence and polygons
                if hasattr(page, "words") and page.words:
                    for w in page.words:
                        span_offset = None
                        span_length = None
                        if hasattr(w, "span") and w.span:
                            span_offset = getattr(w.span, "offset", None)
                            span_length = getattr(w.span, "length", None)

                        words.append(
                            OCRWord(
                                content=getattr(w, "content", ""),
                                confidence=float(getattr(w, "confidence", 1.0) or 1.0),
                                polygon=list(getattr(w, "polygon", []) or []) if hasattr(w, "polygon") else None,
                                span_offset=span_offset,
                                span_length=span_length,
                            )
                        )

                # Extract line-level tokens
                if hasattr(page, "lines") and page.lines:
                    for line in page.lines:
                        lines.append(
                            OCRLine(
                                content=getattr(line, "content", ""),
                                polygon=list(getattr(line, "polygon", []) or []) if hasattr(line, "polygon") else None,
                            )
                        )

        # Fallback if no words parsed from pages but raw_content exists
        if not words and raw_content:
            for token in raw_content.split():
                if token.strip():
                    words.append(OCRWord(content=token.strip(), confidence=1.0))

        return OCRDocument(
            content=raw_content,
            words=words,
            lines=lines,
            width=page_width,
            height=page_height,
            unit=page_unit,
        )

    def extract_text(self, image_bytes: bytes) -> str:
        """Sends image bytes to Azure Document Intelligence and returns plain text."""
        doc = self.extract_document(image_bytes)
        return doc.content
