"""Outbound client for Azure Document Intelligence OCR service."""

import logging
from typing import Optional
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

from app.core.config import settings

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

    def extract_text(self, image_bytes: bytes) -> str:
        """Sends image bytes to Azure Document Intelligence and returns plain text."""
        client = self._get_client()
        logger.info("Calling Azure Document Intelligence (model: %s)", self.model_id)

        poller = client.begin_analyze_document(
            model_id=self.model_id,
            body=image_bytes,
            content_type="application/octet-stream",
        )
        result = poller.result()
        return result.content or ""
