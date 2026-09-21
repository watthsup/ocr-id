"""Pydantic schemas for Thai ID Card OCR and KIE service."""

from typing import Optional
from pydantic import BaseModel, Field


class ThaiName(BaseModel):
    title: Optional[str] = Field(None, description="คำนำหน้านามภาษาไทย เช่น นาย, นาง, นางสาว")
    first_name: Optional[str] = Field(None, description="ชื่อตัว")
    middle_name: Optional[str] = Field(None, description="ชื่อกลาง (ถ้ามี)")
    last_name: Optional[str] = Field(None, description="ชื่อสกุล")
    full_name: Optional[str] = Field(None, description="ชื่อ-นามสกุลเต็ม")


class EnglishName(BaseModel):
    title: Optional[str] = Field(None, description="Title prefix, e.g., Mr., Miss, Mrs.")
    first_name: Optional[str] = Field(None, description="First name")
    middle_name: Optional[str] = Field(None, description="Middle name")
    last_name: Optional[str] = Field(None, description="Last name")
    full_name: Optional[str] = Field(None, description="Full English name")


class DateField(BaseModel):
    raw_text_th: Optional[str] = Field(None, description="ข้อความวันที่ภาษาไทย เช่น 15 ม.ค. 2533")
    raw_text_en: Optional[str] = Field(None, description="ข้อความวันที่ภาษาอังกฤษ เช่น 15 Jan. 1990")
    year_be: Optional[int] = Field(None, description="ปี พ.ศ.")
    year_ce: Optional[int] = Field(None, description="ปี ค.ศ. (A.D.)")
    month: Optional[int] = Field(None, description="เดือน (1-12)")
    day: Optional[int] = Field(None, description="วัน (1-31)")
    iso_date: Optional[str] = Field(None, description="รูปแบบวันที่ ISO YYYY-MM-DD")
    is_lifetime: Optional[bool] = Field(False, description="กรณีวันหมดอายุระบุตลอดชีพ")


class AddressField(BaseModel):
    raw_address: Optional[str] = Field(None, description="ที่อยู่ตามที่ปรากฏบนบัตร")
    house_no: Optional[str] = Field(None, description="บ้านเลขที่")
    moo: Optional[str] = Field(None, description="หมู่ที่")
    trok_soi: Optional[str] = Field(None, description="ตรอก/ซอย")
    road: Optional[str] = Field(None, description="ถนน")
    sub_district: Optional[str] = Field(None, description="ตำบล / แขวง")
    district: Optional[str] = Field(None, description="อำเภอ / เขต")
    province: Optional[str] = Field(None, description="จังหวัด")
    postal_code: Optional[str] = Field(None, description="รหัสไปรษณีย์ 5 หลัก")


# ========================================================
# Front of Card Schemas
# ========================================================

class ThaiIdCardExtraction(BaseModel):
    """Schema enforced by LLM Structured Outputs for card front."""
    identification_number: Optional[str] = Field(None, description="เลขประจำตัวประชาชน 13 หลัก")
    thai_name: Optional[ThaiName] = Field(None, description="ข้อมูลชื่อ-สกุลภาษาไทย")
    english_name: Optional[EnglishName] = Field(None, description="ข้อมูลชื่อ-สกุลภาษาอังกฤษ")
    date_of_birth: Optional[DateField] = Field(None, description="วันเดือนปีเกิด")
    religion: Optional[str] = Field(None, description="ศาสนา")
    address: Optional[AddressField] = Field(None, description="ข้อมูลที่อยู่แยกตามเขตการปกครอง")
    date_of_issue: Optional[DateField] = Field(None, description="วันออกบัตร")
    date_of_expiry: Optional[DateField] = Field(None, description="วันบัตรหมดอายุ")


class ThaiIdCardData(ThaiIdCardExtraction):
    """Final validated response data including checksum status."""
    is_id_checksum_valid: Optional[bool] = Field(None, description="ความถูกต้องของ Checksum เลขบัตร 13 หลัก (mod 11)")


class ThaiIdCardResponse(BaseModel):
    status: str = "success"
    data: Optional[ThaiIdCardData] = None
    processing_time_ms: float = Field(..., description="Processing time (ms)")


# ========================================================
# Back of Card (Laser ID) Schemas
# ========================================================

class ThaiIdCardLaserExtraction(BaseModel):
    """Schema enforced by LLM Structured Outputs for card back (Laser ID)."""
    raw_laser_id: Optional[str] = Field(None, description="รหัส Laser ID 12 ตัวอักษรแบบไม่มีขีด เช่น JT0123456789")
    formatted_laser_id: Optional[str] = Field(None, description="รหัส Laser ID รูปแบบมาตรฐานมีขีด เช่น JT0-1234567-89")


class ThaiIdCardLaserData(ThaiIdCardLaserExtraction):
    """Final response data for Laser ID including format validation."""
    is_laser_id_valid_format: Optional[bool] = Field(None, description="ความถูกต้องตามรูปแบบตัวอักษรภาษาอังกฤษ 2 ตัวแรกตามด้วยตัวเลข 10 ตัว")


class ThaiIdCardLaserResponse(BaseModel):
    status: str = "success"
    data: Optional[ThaiIdCardLaserData] = None
    processing_time_ms: float = Field(..., description="Processing time (ms)")
