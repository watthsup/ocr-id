"""Unit tests for GroundingService, field confidence scoring, and OCR metadata matching."""

import pytest
from app.models.schemas import (
    AddressField,
    DateField,
    EnglishName,
    OCRDocument,
    OCRWord,
    ThaiIdCardExtraction,
    ThaiIdCardLaserExtraction,
    ThaiName,
)
from app.services.grounding_service import GroundingService


@pytest.fixture
def sample_ocr_document() -> OCRDocument:
    raw_content = (
        "1 1007 01234 56 1\n"
        "นายสมชาย ใจดี\n"
        "Mr. Somchai Jaidee\n"
        "เกิดวันที่ 15 ม.ค. 2533\n"
        "15 Jan. 1990\n"
        "ศาสนา พุทธ\n"
        "99/1 หมู่ที่ 2 ต.บางตลาด อ.ปากเกร็ด จ.นนทบุรี 11120\n"
        "วันออกบัตร 20 ก.พ. 2564\n"
        "วันหมดอายุ 14 ม.ค. 2572\n"
    )

    words = [
        # ID Number
        OCRWord(content="1", confidence=0.99, polygon=[80, 100, 95, 100, 95, 120, 80, 120]),
        OCRWord(content="1007", confidence=0.98, polygon=[105, 100, 160, 100, 160, 120, 105, 120]),
        OCRWord(content="01234", confidence=0.97, polygon=[170, 100, 240, 100, 240, 120, 170, 120]),
        OCRWord(content="56", confidence=0.99, polygon=[250, 100, 280, 100, 280, 120, 250, 120]),
        OCRWord(content="1", confidence=0.95, polygon=[290, 100, 305, 100, 305, 120, 290, 120]),
        # Thai Name
        OCRWord(content="นายสมชาย", confidence=0.96, polygon=[260, 160, 350, 160, 350, 185, 260, 185]),
        OCRWord(content="ใจดี", confidence=0.94, polygon=[360, 160, 420, 160, 420, 185, 360, 185]),
        # English Name
        OCRWord(content="Mr.", confidence=0.99, polygon=[260, 200, 300, 200, 300, 220, 260, 220]),
        OCRWord(content="Somchai", confidence=0.97, polygon=[310, 200, 390, 200, 390, 220, 310, 220]),
        OCRWord(content="Jaidee", confidence=0.96, polygon=[400, 200, 470, 200, 470, 220, 400, 220]),
        # DOB
        OCRWord(content="15", confidence=0.98),
        OCRWord(content="ม.ค.", confidence=0.95),
        OCRWord(content="2533", confidence=0.99),
        # Religion
        OCRWord(content="พุทธ", confidence=0.96),
        # Address
        OCRWord(content="99/1", confidence=0.98),
        OCRWord(content="หมู่ที่", confidence=0.95),
        OCRWord(content="2", confidence=0.99),
        OCRWord(content="ต.บางตลาด", confidence=0.94),
        OCRWord(content="อ.ปากเกร็ด", confidence=0.96),
        OCRWord(content="จ.นนทบุรี", confidence=0.98),
        OCRWord(content="11120", confidence=0.99),
        # Dates
        OCRWord(content="20", confidence=0.98),
        OCRWord(content="ก.พ.", confidence=0.95),
        OCRWord(content="2564", confidence=0.99),
        OCRWord(content="14", confidence=0.98),
        OCRWord(content="2572", confidence=0.99),
    ]

    return OCRDocument(content=raw_content, words=words)


def test_grounding_thai_id_card_high_confidence(sample_ocr_document):
    grounding = GroundingService(confidence_threshold=0.80)

    extracted = ThaiIdCardExtraction(
        raw_identification_number="1 1007 01234 56 1",
        identification_number="1100701234561",
        thai_name=ThaiName(
            raw_text="นายสมชาย ใจดี",
            title="นาย",
            first_name="สมชาย",
            last_name="ใจดี",
            full_name="นายสมชาย ใจดี",
        ),
        english_name=EnglishName(
            raw_text="Mr. Somchai Jaidee",
            title="Mr.",
            first_name="Somchai",
            last_name="Jaidee",
            full_name="Mr. Somchai Jaidee",
        ),
        date_of_birth=DateField(
            raw_text_th="15 ม.ค. 2533",
            raw_text_en="15 Jan. 1990",
            day=15,
            month=1,
            year_be=2533,
            year_ce=1990,
            iso_date="1990-01-15",
        ),
        raw_religion="พุทธ",
        religion="พุทธ",
        address=AddressField(
            raw_address="99/1 หมู่ที่ 2 ต.บางตลาด อ.ปากเกร็ด จ.นนทบุรี 11120",
            house_no="99/1",
            moo="2",
            sub_district="บางตลาด",
            district="ปากเกร็ด",
            province="นนทบุรี",
            postal_code="11120",
        ),
        date_of_issue=DateField(raw_text_th="20 ก.พ. 2564", year_be=2564, year_ce=2021, iso_date="2021-02-20"),
        date_of_expiry=DateField(raw_text_th="14 ม.ค. 2572", year_be=2572, year_ce=2029, iso_date="2029-01-14"),
    )

    summary = grounding.ground_thai_id_card(
        extracted=extracted,
        ocr_doc=sample_ocr_document,
        is_id_checksum_valid=True,
    )

    assert summary.overall_confidence >= 0.80
    assert summary.is_overall_confident is True
    assert summary.confident_fields_count == summary.total_fields
    assert len(summary.fields_needing_review) == 0

    id_field = summary.fields["identification_number"]
    assert id_field.is_confident is True
    assert id_field.verification == "in_source"
    assert id_field.polygon is not None
    assert id_field.confidence >= 0.95

    th_field = summary.fields["thai_name"]
    assert th_field.is_confident is True
    assert th_field.verification == "in_source"


def test_grounding_low_confidence_and_checksum_failure(sample_ocr_document):
    grounding = GroundingService(confidence_threshold=0.85)

    extracted = ThaiIdCardExtraction(
        raw_identification_number="1 1007 01234 56 0",
        identification_number="1100701234560",  # Invalid checksum
        thai_name=ThaiName(
            raw_text="นายสมชาย ใจดี",
            full_name="นายสมชาย ใจดี",
        ),
        # Field completely absent from OCR
        english_name=EnglishName(
            raw_text="Unknown Person Name",
            full_name="Unknown Person Name",
        ),
    )

    summary = grounding.ground_thai_id_card(
        extracted=extracted,
        ocr_doc=sample_ocr_document,
        is_id_checksum_valid=False,  # Failed checksum
    )

    assert summary.is_overall_confident is False
    assert "identification_number" in summary.fields_needing_review
    assert "english_name" in summary.fields_needing_review

    # Checksum failure should flag issue
    id_fc = summary.fields["identification_number"]
    assert any("checksum" in iss.lower() for iss in id_fc.issues)
    assert id_fc.is_confident is False

    # English name should be flagged not_in_source or low confidence
    en_fc = summary.fields["english_name"]
    assert en_fc.is_confident is False
    assert en_fc.verification == "not_in_source"


def test_grounding_laser_id():
    grounding = GroundingService(confidence_threshold=0.80)

    ocr_doc = OCRDocument(
        content="JT0 - 1234567 - 89\nกรมการปกครอง",
        words=[
            OCRWord(content="JT0", confidence=0.98),
            OCRWord(content="1234567", confidence=0.99),
            OCRWord(content="89", confidence=0.97),
        ],
    )

    extracted = ThaiIdCardLaserExtraction(
        raw_text="JT0 - 1234567 - 89",
        raw_laser_id="JT0123456789",
        formatted_laser_id="JT0-1234567-89",
    )

    summary = grounding.ground_laser_id(
        extracted=extracted,
        ocr_doc=ocr_doc,
        is_laser_id_valid_format=True,
    )

    assert summary.is_overall_confident is True
    assert summary.fields["laser_id"].confidence >= 0.95
    assert summary.fields["laser_id"].verification == "in_source"
