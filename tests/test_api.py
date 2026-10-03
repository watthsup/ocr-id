"""Integration tests for simplified FastAPI endpoints."""

import base64
import io
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.api.v1.endpoints.id_card import get_pipeline_service
from app.clients.ocr_client import AzureOCRClient
from app.models.schemas import ThaiIdCardExtraction, ThaiIdCardLaserExtraction
from app.services.kie_service import KIEService
from app.services.pipeline_service import PipelineService


@pytest.fixture
def sample_image_bytes() -> bytes:
    """Creates a minimal valid RGB JPEG image in-memory."""
    img = Image.new("RGB", (200, 100), color=(255, 255, 255))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture
def mock_pipeline_service():
    """Provides a mocked PipelineService with simulated Azure OCR and LLM outputs."""
    mock_ocr = MagicMock(spec=AzureOCRClient)
    mock_ocr.extract_text.return_value = (
        "1 1007 01234 56 1\nนายสมชาย ใจดี\nMr. Somchai Jaidee\nเกิด 15 ม.ค. 2533\n99/1 หมู่ 2 ต.บางตลาด อ.ปากเกร็ด จ.นนทบุรี 11120"
    )

    mock_kie = MagicMock(spec=KIEService)
    mock_kie.extract.return_value = ThaiIdCardExtraction(
        identification_number="1100701234561",
        thai_name={
            "title": "นาย",
            "first_name": "สมชาย",
            "middle_name": None,
            "last_name": "ใจดี",
            "full_name": "นายสมชาย ใจดี",
        },
        english_name={
            "title": "Mr.",
            "first_name": "Somchai",
            "middle_name": None,
            "last_name": "Jaidee",
            "full_name": "Mr. Somchai Jaidee",
        },
        date_of_birth={
            "raw_text_th": "15 ม.ค. 2533",
            "raw_text_en": "15 Jan. 1990",
            "day": 15,
            "month": 1,
            "year_be": 2533,
            "year_ce": 1990,
            "iso_date": "1990-01-15",
        },
        religion="พุทธ",
        address={
            "raw_address": "99/1 หมู่ที่ 2 ต.บางตลาด อ.ปากเกร็ด จ.นนทบุรี 11120",
            "house_no": "99/1",
            "moo": "2",
            "trok_soi": None,
            "road": None,
            "sub_district": "บางตลาด",
            "district": "ปากเกร็ด",
            "province": "นนทบุรี",
            "postal_code": "11120",
        },
        date_of_issue={
            "raw_text_th": "20 ก.พ. 2564",
            "raw_text_en": "20 Feb. 2021",
            "day": 20,
            "month": 2,
            "year_be": 2564,
            "year_ce": 2021,
            "iso_date": "2021-02-20",
        },
        date_of_expiry={
            "raw_text_th": "14 ม.ค. 2572",
            "raw_text_en": "14 Jan. 2029",
            "day": 14,
            "month": 1,
            "year_be": 2572,
            "year_ce": 2029,
            "iso_date": "2029-01-14",
            "is_lifetime": False,
        },
    )

    mock_kie.extract_laser_id.return_value = ThaiIdCardLaserExtraction(
        raw_laser_id="JT0123456789",
        formatted_laser_id="JT0-1234567-89",
    )

    pipeline = PipelineService(ocr_client=mock_ocr, kie_service=mock_kie)
    return pipeline


@pytest.fixture
def client(mock_pipeline_service):
    app.dependency_overrides[get_pipeline_service] = lambda: mock_pipeline_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_realtime_id_card_multipart_upload(client, sample_image_bytes):
    response = client.post(
        "/api/v1/ocr/id-card",
        files={"file": ("thai_id.jpg", sample_image_bytes, "image/jpeg")},
    )
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "success"
    assert res["data"]["identification_number"] == "1100701234561"
    assert res["data"]["is_id_checksum_valid"] is True
    assert res["data"]["thai_name"]["full_name"] == "นายสมชาย ใจดี"
    assert res["data"]["english_name"]["full_name"] == "Mr. Somchai Jaidee"
    assert res["data"]["address"]["province"] == "นนทบุรี"
    assert res["processing_time_ms"] >= 0
    assert "confidence_summary" in res["data"]
    assert res["data"]["confidence_summary"]["overall_confidence"] > 0
    assert "stages" in res and len(res["stages"]) == 5
    assert "timings_ms" in res and "ocr" in res["timings_ms"]


def test_realtime_id_card_base64_payload(client, sample_image_bytes):
    b64_str = base64.b64encode(sample_image_bytes).decode("utf-8")
    payload = {"image_base64": f"data:image/jpeg;base64,{b64_str}"}

    response = client.post("/api/v1/ocr/id-card", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "success"
    assert res["data"]["identification_number"] == "1100701234561"


def test_empty_request_bad_request(client):
    response = client.post("/api/v1/ocr/id-card")
    assert response.status_code == 400


def test_corrupt_image_error(client):
    response = client.post(
        "/api/v1/ocr/id-card",
        files={"file": ("bad.jpg", b"invalid-bytes", "image/jpeg")},
    )
    assert response.status_code in (422, 400)


def test_realtime_laser_id_multipart_upload(client, sample_image_bytes):
    response = client.post(
        "/api/v1/ocr/laser-id",
        files={"file": ("thai_id_back.jpg", sample_image_bytes, "image/jpeg")},
    )
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "success"
    assert res["data"]["raw_laser_id"] == "JT0123456789"
    assert res["data"]["formatted_laser_id"] == "JT0-1234567-89"
    assert res["data"]["is_laser_id_valid_format"] is True
    assert res["processing_time_ms"] >= 0
    assert "confidence_summary" in res["data"]
    assert "stages" in res and len(res["stages"]) == 5


def test_realtime_laser_id_base64_payload(client, sample_image_bytes):
    b64_str = base64.b64encode(sample_image_bytes).decode("utf-8")
    payload = {"image_base64": f"data:image/jpeg;base64,{b64_str}"}

    response = client.post("/api/v1/ocr/laser-id", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "success"
    assert res["data"]["formatted_laser_id"] == "JT0-1234567-89"

