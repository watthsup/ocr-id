"""Pydantic schemas for Thai ID Card OCR and KIE service with Grounding & Confidence Scoring."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


# ========================================================
# Azure Document Intelligence OCR Metadata Schemas
# ========================================================

class OCRWord(BaseModel):
    """Word token with bounding polygon and confidence score from Azure Document Intelligence."""
    content: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    polygon: Optional[List[float]] = None
    span_offset: Optional[int] = None
    span_length: Optional[int] = None


class OCRLine(BaseModel):
    """Text line with polygon from Azure Document Intelligence."""
    content: str
    polygon: Optional[List[float]] = None


class OCRDocument(BaseModel):
    """Full structured output from Azure Document Intelligence OCR analysis."""
    content: str = ""
    words: List[OCRWord] = Field(default_factory=list)
    lines: List[OCRLine] = Field(default_factory=list)
    width: Optional[float] = None
    height: Optional[float] = None
    unit: Optional[str] = None


# ========================================================
# Grounding & Confidence Scoring Schemas
# ========================================================

class FieldConfidence(BaseModel):
    """Grounding & confidence metrics for an individual extracted field."""
    field_code: str = Field(..., description="Unique field identifier, e.g. 'identification_number'")
    field_name_en: str = Field("", description="English label for UI display")
    field_name_th: str = Field("", description="Thai label for UI display")
    raw_text: Optional[str] = Field(None, description="Verbatim text from OCR output before normalization")
    normalized_value: Optional[str] = Field(None, description="Cleaned and standardized field value")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Calculated confidence score (0.0 - 1.0)")
    confidence_percentage: float = Field(..., description="Confidence score expressed as a percentage (0 - 100)")
    is_confident: bool = Field(..., description="True if confidence >= configured CONFIDENCE_THRESHOLD")
    verification: str = Field("in_source", description="Source verification status: 'in_source', 'not_in_source', 'derived'")
    status: str = Field("confident", description="Status indicator: 'confident', 'needs_review', 'not_found'")
    polygon: Optional[List[float]] = Field(None, description="Bounding polygon coordinates [x1, y1, ...] from OCR metadata")
    issues: List[str] = Field(default_factory=list, description="Validation issues, OCR noise corrections, or warnings")


class ConfidenceSummary(BaseModel):
    """Overall confidence score and grounding breakdown across all fields."""
    overall_confidence: float = Field(..., description="Average confidence score across all fields (0.0 - 1.0)")
    overall_confidence_percentage: float = Field(..., description="Overall confidence percentage (0 - 100)")
    confidence_threshold: float = Field(..., description="Threshold applied from configuration (CONFIDENCE_THRESHOLD)")
    is_overall_confident: bool = Field(..., description="True if overall_confidence >= confidence_threshold and no critical errors")
    total_fields: int = Field(0, description="Total number of evaluated fields")
    confident_fields_count: int = Field(0, description="Number of fields meeting or exceeding the threshold")
    review_fields_count: int = Field(0, description="Number of fields requiring human review")
    fields: Dict[str, FieldConfidence] = Field(default_factory=dict, description="Field-by-field confidence metrics")
    fields_needing_review: List[str] = Field(default_factory=list, description="List of field codes that require review")


class StageTiming(BaseModel):
    """Timing for an individual pipeline execution stage."""
    key: str
    label: str
    status: str = "done"  # "pending", "running", "done", "failed"
    ms: Optional[float] = None


# ========================================================
# Front of Card Schemas
# ========================================================

class ThaiName(BaseModel):
    raw_text: Optional[str] = Field(None, description="ข้อความชื่อ-สกุลภาษาไทยดิบจาก OCR ก่อน normalization")
    title: Optional[str] = Field(None, description="คำนำหน้านามภาษาไทย เช่น นาย, นาง, นางสาว")
    first_name: Optional[str] = Field(None, description="ชื่อตัว")
    middle_name: Optional[str] = Field(None, description="ชื่อกลาง (ถ้ามี)")
    last_name: Optional[str] = Field(None, description="ชื่อสกุล")
    full_name: Optional[str] = Field(None, description="ชื่อ-นามสกุลเต็ม")
    confidence: Optional[float] = Field(None, description="Confidence score (0.0 - 1.0)")
    is_confident: Optional[bool] = Field(None, description="Whether confidence meets threshold")


class EnglishName(BaseModel):
    raw_text: Optional[str] = Field(None, description="Raw English name string from OCR before normalization")
    title: Optional[str] = Field(None, description="Title prefix, e.g., Mr., Miss, Mrs.")
    first_name: Optional[str] = Field(None, description="First name")
    middle_name: Optional[str] = Field(None, description="Middle name")
    last_name: Optional[str] = Field(None, description="Last name")
    full_name: Optional[str] = Field(None, description="Full English name")
    confidence: Optional[float] = Field(None, description="Confidence score (0.0 - 1.0)")
    is_confident: Optional[bool] = Field(None, description="Whether confidence meets threshold")


class DateField(BaseModel):
    raw_text_th: Optional[str] = Field(None, description="ข้อความวันที่ภาษาไทยดิบจาก OCR เช่น 15 ม.ค. 2533")
    raw_text_en: Optional[str] = Field(None, description="ข้อความวันที่ภาษาอังกฤษดิบจาก OCR เช่น 15 Jan. 1990")
    year_be: Optional[int] = Field(None, description="ปี พ.ศ.")
    year_ce: Optional[int] = Field(None, description="ปี ค.ศ. (A.D.)")
    month: Optional[int] = Field(None, description="เดือน (1-12)")
    day: Optional[int] = Field(None, description="วัน (1-31)")
    iso_date: Optional[str] = Field(None, description="รูปแบบวันที่ ISO YYYY-MM-DD")
    is_lifetime: Optional[bool] = Field(False, description="กรณีวันหมดอายุระบุตลอดชีพ")
    confidence: Optional[float] = Field(None, description="Confidence score (0.0 - 1.0)")
    is_confident: Optional[bool] = Field(None, description="Whether confidence meets threshold")


class AddressField(BaseModel):
    raw_address: Optional[str] = Field(None, description="ที่อยู่ตามที่ปรากฏบนบัตรดิบจาก OCR")
    house_no: Optional[str] = Field(None, description="บ้านเลขที่")
    moo: Optional[str] = Field(None, description="หมู่ที่")
    trok_soi: Optional[str] = Field(None, description="ตรอก/ซอย")
    road: Optional[str] = Field(None, description="ถนน")
    sub_district: Optional[str] = Field(None, description="ตำบล / แขวง")
    district: Optional[str] = Field(None, description="อำเภอ / เขต")
    province: Optional[str] = Field(None, description="จังหวัด")
    postal_code: Optional[str] = Field(None, description="รหัสไปรษณีย์ 5 หลัก")
    confidence: Optional[float] = Field(None, description="Confidence score (0.0 - 1.0)")
    is_confident: Optional[bool] = Field(None, description="Whether confidence meets threshold")


class ThaiIdCardExtraction(BaseModel):
    """Schema enforced by LLM Structured Outputs for card front."""
    raw_identification_number: Optional[str] = Field(None, description="เลขประจำตัวประชาชนดิบจาก OCR เช่น 1 1007 01234 56 1")
    identification_number: Optional[str] = Field(None, description="เลขประจำตัวประชาชน 13 หลักที่ทำ normalization แล้ว")
    thai_name: Optional[ThaiName] = Field(None, description="ข้อมูลชื่อ-สกุลภาษาไทย")
    english_name: Optional[EnglishName] = Field(None, description="ข้อมูลชื่อ-สกุลภาษาอังกฤษ")
    date_of_birth: Optional[DateField] = Field(None, description="วันเดือนปีเกิด")
    raw_religion: Optional[str] = Field(None, description="ข้อความศาสนาดิบจาก OCR")
    religion: Optional[str] = Field(None, description="ศาสนา")
    address: Optional[AddressField] = Field(None, description="ข้อมูลที่อยู่แยกตามเขตการปกครอง")
    date_of_issue: Optional[DateField] = Field(None, description="วันออกบัตร")
    date_of_expiry: Optional[DateField] = Field(None, description="วันบัตรหมดอายุ")


class ThaiIdCardData(ThaiIdCardExtraction):
    """Final validated response data including checksum status and confidence summary."""
    is_id_checksum_valid: Optional[bool] = Field(None, description="ความถูกต้องของ Checksum เลขบัตร 13 หลัก (mod 11)")
    confidence_summary: Optional[ConfidenceSummary] = Field(None, description="Grounding & Confidence Summary")


class ThaiIdCardResponse(BaseModel):
    status: str = "success"
    data: Optional[ThaiIdCardData] = None
    stages: List[StageTiming] = Field(default_factory=list, description="Granular execution breakdown per pipeline stage")
    timings_ms: Dict[str, float] = Field(default_factory=dict, description="Detailed stage timings in milliseconds")
    processing_time_ms: float = Field(..., description="Total processing time (ms)")


# ========================================================
# Back of Card (Laser ID) Schemas
# ========================================================

class ThaiIdCardLaserExtraction(BaseModel):
    """Schema enforced by LLM Structured Outputs for card back (Laser ID)."""
    raw_text: Optional[str] = Field(None, description="ข้อความ Laser ID ดิบจาก OCR เช่น JT0 - 1234567 - 89 หรือ JT0123456789")
    raw_laser_id: Optional[str] = Field(None, description="รหัส Laser ID 12 ตัวอักษรแบบไม่มีขีด เช่น JT0123456789")
    formatted_laser_id: Optional[str] = Field(None, description="รหัส Laser ID รูปแบบมาตรฐานมีขีด เช่น JT0-1234567-89")


class ThaiIdCardLaserData(ThaiIdCardLaserExtraction):
    """Final response data for Laser ID including format validation and confidence."""
    is_laser_id_valid_format: Optional[bool] = Field(None, description="ความถูกต้องตามรูปแบบตัวอักษรภาษาอังกฤษ 2 ตัวแรกตามด้วยตัวเลข 10 ตัว")
    confidence_summary: Optional[ConfidenceSummary] = Field(None, description="Grounding & Confidence Summary for Laser ID")


class ThaiIdCardLaserResponse(BaseModel):
    status: str = "success"
    data: Optional[ThaiIdCardLaserData] = None
    stages: List[StageTiming] = Field(default_factory=list, description="Granular execution breakdown per pipeline stage")
    timings_ms: Dict[str, float] = Field(default_factory=dict, description="Detailed stage timings in milliseconds")
    processing_time_ms: float = Field(..., description="Total processing time (ms)")
