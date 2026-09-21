from typing import Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application Settings
    APP_NAME: str = "Thai ID Card OCR & KIE API"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    PORT: int = 8000

    # 1. OCR Engine: Azure Document Intelligence
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT: str = "https://placeholder-ocr.cognitiveservices.azure.com/"
    AZURE_DOCUMENT_INTELLIGENCE_KEY: str = "placeholder_azure_key"
    AZURE_DOCUMENT_INTELLIGENCE_MODEL_ID: str = "prebuilt-layout"

    # 2. LLM KIE Provider Selection
    LLM_PROVIDER: Literal["openai", "azure_foundry"] = "openai"

    # OpenAI Settings
    OPENAI_API_KEY: str = "sk-placeholder-key"
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TEMPERATURE: float = 0.0

    # Azure AI Foundry / Azure OpenAI Settings
    AZURE_FOUNDRY_ENDPOINT: Optional[str] = None
    AZURE_FOUNDRY_API_KEY: Optional[str] = None
    AZURE_FOUNDRY_DEPLOYMENT_NAME: str = "gpt-4o-mini"
    AZURE_FOUNDRY_API_VERSION: str = "2024-08-01-preview"

    # Processing & Validation Flags
    DEFAULT_VALIDATE_CHECKSUM: bool = True
    MAX_IMAGE_SIZE_MB: int = 10


settings = Settings()
