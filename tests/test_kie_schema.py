"""Unit tests for Pydantic Structured Outputs schema and KIEService."""

import pytest
from unittest.mock import MagicMock
from app.clients.llm_client import LLMClient
from app.models.schemas import (
    AddressField,
    DateField,
    EnglishName,
    ThaiIdCardData,
    ThaiIdCardExtraction,
    ThaiName,
)
from app.services.kie_service import KIEService


def test_schema_instantiation():
    extracted = ThaiIdCardExtraction(
        identification_number="1100701234561",
        thai_name=ThaiName(title="นาย", first_name="สมชาย", last_name="ใจดี", full_name="นายสมชาย ใจดี"),
        english_name=EnglishName(title="Mr.", first_name="Somchai", last_name="Jaidee", full_name="Mr. Somchai Jaidee"),
        date_of_birth=DateField(day=15, month=1, year_be=2533, year_ce=1990, iso_date="1990-01-15"),
        address=AddressField(house_no="99/1", moo="2", sub_district="บางตลาด", district="ปากเกร็ด", province="นนทบุรี", postal_code="11120"),
    )

    card_data = ThaiIdCardData(**extracted.model_dump(), is_id_checksum_valid=True)
    assert card_data.identification_number == "1100701234561"
    assert card_data.is_id_checksum_valid is True
    assert card_data.thai_name.first_name == "สมชาย"
    assert card_data.date_of_birth.year_ce == 1990
    assert card_data.address.province == "นนทบุรี"


def test_kie_service_structured_output():
    mock_llm = MagicMock(spec=LLMClient)
    expected_extraction = ThaiIdCardExtraction(
        identification_number="1100701234561",
        thai_name=ThaiName(title="นาย", first_name="สมชาย", last_name="ใจดี"),
        religion="พุทธ",
    )
    mock_llm.chat_completion_structured.return_value = expected_extraction

    kie_service = KIEService(llm_client=mock_llm)
    result = kie_service.extract("Raw OCR text")

    assert isinstance(result, ThaiIdCardExtraction)
    assert result.identification_number == "1100701234561"
    assert result.religion == "พุทธ"
    mock_llm.chat_completion_structured.assert_called_once()


def test_kie_service_laser_id_structured_output():
    from app.models.schemas import ThaiIdCardLaserExtraction

    mock_llm = MagicMock(spec=LLMClient)
    expected = ThaiIdCardLaserExtraction(
        raw_laser_id="JT0123456789",
        formatted_laser_id="JT0-1234567-89",
    )
    mock_llm.chat_completion_structured.return_value = expected

    kie_service = KIEService(llm_client=mock_llm)
    result = kie_service.extract_laser_id("Back card OCR text")

    assert isinstance(result, ThaiIdCardLaserExtraction)
    assert result.raw_laser_id == "JT0123456789"
    assert result.formatted_laser_id == "JT0-1234567-89"
    mock_llm.chat_completion_structured.assert_called_once()
