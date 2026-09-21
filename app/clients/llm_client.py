"""Outbound client for LLM providers with native Structured Outputs support."""

import logging
from typing import Any, Dict, List, Literal, Optional, Type, TypeVar
from openai import AzureOpenAI, OpenAI
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    """Outbound adapter handling LLM Structured Outputs via Pydantic schema."""

    def __init__(self, provider: Optional[Literal["openai", "azure_foundry"]] = None):
        self.provider = provider or settings.LLM_PROVIDER
        self._openai_client: Optional[OpenAI] = None
        self._foundry_client: Optional[AzureOpenAI] = None

    def _get_openai_client(self) -> OpenAI:
        if self._openai_client is None:
            self._openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        return self._openai_client

    def _get_foundry_client(self) -> AzureOpenAI:
        if self._foundry_client is None:
            endpoint = settings.AZURE_FOUNDRY_ENDPOINT
            api_key = settings.AZURE_FOUNDRY_API_KEY
            if not endpoint or not api_key:
                raise ValueError(
                    "Azure AI Foundry endpoint or key is missing in configuration."
                )
            self._foundry_client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version=settings.AZURE_FOUNDRY_API_VERSION,
            )
        return self._foundry_client

    def chat_completion_structured(
        self,
        messages: List[Dict[str, str]],
        response_model: Type[T],
        temperature: Optional[float] = None,
    ) -> T:
        """Invokes LLM with native Structured Outputs using Pydantic response_format."""
        temp = temperature if temperature is not None else settings.OPENAI_TEMPERATURE

        if self.provider == "azure_foundry":
            logger.info("Calling Azure AI Foundry with Structured Outputs (deployment: %s)", settings.AZURE_FOUNDRY_DEPLOYMENT_NAME)
            client = self._get_foundry_client()
            response = client.chat.completions.parse(
                model=settings.AZURE_FOUNDRY_DEPLOYMENT_NAME,
                temperature=temp,
                response_format=response_model,
                messages=messages,
            )
        else:
            logger.info("Calling OpenAI with Structured Outputs (model: %s)", settings.OPENAI_MODEL)
            client = self._get_openai_client()
            response = client.chat.completions.parse(
                model=settings.OPENAI_MODEL,
                temperature=temp,
                response_format=response_model,
                messages=messages,
            )

        parsed = response.choices[0].message.parsed
        if parsed is None:
            raise ValueError("LLM failed to return valid structured data conforming to schema.")
        return parsed
