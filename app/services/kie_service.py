"""Key Information Extraction (KIE) service for Thai National ID cards using Structured Outputs."""

import logging
from typing import Optional

from app.clients.llm_client import LLMClient
from app.models.schemas import ThaiIdCardExtraction, ThaiIdCardLaserExtraction

logger = logging.getLogger(__name__)

KIE_FRONT_SYSTEM_PROMPT = """You are an expert AI specialized in Thai National ID Card Key Information Extraction (KIE).
Your task is to analyze the OCR text from the front of a Thai National ID card and extract all key information into the specified schema.

CRITICAL DUAL-EXTRACTION INSTRUCTION:
For each key field, extract BOTH:
1. The exact raw text (`raw_text`, `raw_identification_number`, `raw_religion`, etc.) VERBATIM as printed in the OCR text, preserving all spaces, typos, punctuation, and OCR misreads. This is required for OCR metadata grounding and confidence scoring.
2. The normalized, cleaned, and standardized fields where you intelligently correct OCR misreads, fix typos, format dates, and parse sub-components.

Extraction & Interpretation Guidelines:
1. Identification Number:
   - raw_identification_number: The verbatim text snippet from the OCR (e.g. "1 1007 01234 56 1" or "1-1007-01234-56-1").
   - identification_number: The standardized 13-digit numeric string with all spaces and dashes stripped (e.g. "1100701234561").

2. Names & Titles:
   - thai_name:
     * raw_text: The verbatim Thai name line as seen in OCR (e.g. "นายสมชาย ใจดี" or "นาย สมชาย  ใจดี").
     * title: Title prefix (คำนำหน้านาม เช่น นาย, นาง, นางสาว, ด.ช., ด.ญ.).
     * first_name: First name (ชื่อตัว) - do NOT duplicate the title here.
     * middle_name: Middle name (ชื่อกลาง) if present, else null.
     * last_name: Last name (ชื่อสกุล).
     * full_name: Complete full name with title, first, middle, last.
   - english_name:
     * raw_text: The verbatim English name line as seen in OCR (e.g. "Mr. Somchai Jaidee").
     * title: Title prefix (e.g. Mr., Mrs., Miss).
     * first_name, middle_name, last_name, full_name.

3. Dates & Calendar Era:
   - Extract raw_text_th (e.g. "15 ม.ค. 2533") and raw_text_en (e.g. "15 Jan. 1990").
   - Extract day (1-31), month number (1-12), Buddhist Era year (พ.ศ., e.g. 2533), and Common Era year (A.D. / ค.ศ., e.g. 1990).
   - Use the formula: year_ce = year_be - 543 (e.g. 2533 - 543 = 1990).
   - Format iso_date as "YYYY-MM-DD" using year_ce.
   - For expiry date: If the card states "ตลอดชีพ" or "Lifetime", set is_lifetime to true, with date numbers as null.

4. Religion:
   - raw_religion: The verbatim religion text from OCR (e.g. "พุทธ", "อิสลาม", "คริสต์").
   - religion: Normalized religion string.

5. Address Decomposition:
   - raw_address: The verbatim address string as detected in the OCR text.
   - Parse into official administrative subdivisions without prefixes:
     * house_no: House / unit number (เลขที่)
     * moo: Village number (หมู่ที่) without prefix words
     * trok_soi: Trok or Soi without prefix
     * road: Road name without 'ถนน' / 'ถ.' prefix
     * sub_district: Tambon (ตำบล) for upcountry or Khwaeng (แขวง) for Bangkok, without prefix
     * district: Amphoe (อำเภอ) for upcountry or Khet (เขต) for Bangkok, without prefix
     * province: Official province name without prefix (e.g. นนทบุรี, กรุงเทพมหานคร)
     * postal_code: 5-digit postal code

6. OCR Error Handling & Normalization:
   - Correct typical Thai OCR errors in normalized fields such as misplaced vowel/tone marks or confusing characters (e.g., '0' vs 'O', '1' vs 'l', 'ข' vs 'ช')."""


KIE_LASER_SYSTEM_PROMPT = """You are an expert AI specialized in Thai National ID Card Laser Code Extraction (from the back of the card).
Your task is to analyze the OCR text from the back of a Thai National ID card and extract the Laser ID code into the specified schema.

CRITICAL DUAL-EXTRACTION INSTRUCTION:
Extract BOTH:
1. `raw_text`: The verbatim text snippet from the OCR output as seen (e.g. "JT0 - 1234567 - 89" or "JTO 1234567 89").
2. `raw_laser_id`: The continuous 12-character alphanumeric string without hyphens or spaces (e.g. "JT0123456789").
3. `formatted_laser_id`: The standard formatted string with hyphens (e.g. "JT0-1234567-89").

Laser ID Specifications:
1. The Laser ID consists of 12 alphanumeric characters:
   - First 2 characters: strictly English capital letters (e.g. JT, ME, JC).
   - Following 10 characters: strictly numeric digits (0-9).
2. Standard display format is "XX0-XXXXXXX-XX".
3. OCR Error Correction:
   - For the first 2 characters (strictly letters): resolve character confusion, e.g. '0' is 'O' or 'D', '1' is 'I'.
   - For the last 10 characters (strictly digits): 'O' is '0', 'I' or 'l' is '1', 'B' is '8', 'S' is '5'.
   - Ignore barcodes, blank serial numbers, or general legal notice text on the back."""


class KIEService:
    """Business service for extracting Thai ID Card key information using LLM Structured Outputs."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()

    def extract(self, ocr_text: str) -> ThaiIdCardExtraction:
        """Extracts structured Thai ID card front data directly into a validated Pydantic model."""
        messages = [
            {"role": "system", "content": KIE_FRONT_SYSTEM_PROMPT},
            {"role": "user", "content": f"Thai National ID Card Front OCR Content:\n```text\n{ocr_text}\n```"},
        ]

        logger.info("Executing LLM Key Information Extraction (Front) with Structured Outputs")
        return self.llm_client.chat_completion_structured(
            messages=messages,
            response_model=ThaiIdCardExtraction,
        )

    def extract_laser_id(self, ocr_text: str) -> ThaiIdCardLaserExtraction:
        """Extracts Thai ID card Laser ID (back of card) directly into a validated Pydantic model."""
        messages = [
            {"role": "system", "content": KIE_LASER_SYSTEM_PROMPT},
            {"role": "user", "content": f"Thai National ID Card Back OCR Content:\n```text\n{ocr_text}\n```"},
        ]

        logger.info("Executing LLM Laser ID Extraction (Back) with Structured Outputs")
        return self.llm_client.chat_completion_structured(
            messages=messages,
            response_model=ThaiIdCardLaserExtraction,
        )
