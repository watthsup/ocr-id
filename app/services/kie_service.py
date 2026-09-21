"""Key Information Extraction (KIE) service for Thai National ID cards using Structured Outputs."""

import logging
from typing import Optional

from app.clients.llm_client import LLMClient
from app.models.schemas import ThaiIdCardExtraction, ThaiIdCardLaserExtraction

logger = logging.getLogger(__name__)

KIE_FRONT_SYSTEM_PROMPT = """You are an expert AI specialized in Thai National ID Card Key Information Extraction (KIE).
Your task is to analyze the OCR text from the front of a Thai National ID card and extract all key information into the specified schema.

Extraction & Interpretation Guidelines:
1. Identification Number:
   - Extract the 13-digit Thai National ID number.
   - Strip all spaces, dashes, or separators into a continuous 13-digit string.

2. Names & Titles:
   - Cleanly separate the title (คำนำหน้านาม เช่น นาย, นาง, นางสาว, ด.ช., ด.ญ., Mr., Mrs., Miss) from the first name.
   - Do NOT duplicate the title inside first_name.
   - Provide full_name with title, first name, middle name (if any), and last name.

3. Dates & Calendar Era:
   - Extract day (1-31), month number (1-12), Buddhist Era year (พ.ศ., e.g. 2533), and Common Era year (A.D. / ค.ศ., e.g. 1990).
   - Use the formula: year_ce = year_be - 543 (e.g. 2533 - 543 = 1990).
   - Format iso_date as "YYYY-MM-DD" using year_ce.
   - For expiry date: If the card states "ตลอดชีพ" or "Lifetime", set is_lifetime to true, with date numbers as null.

4. Address Decomposition:
   - Parse the address into official administrative subdivisions:
     * house_no: House / unit number (เลขที่)
     * moo: Village number (หมู่ที่) without prefix words
     * trok_soi: Trok or Soi without prefix
     * road: Road name without 'ถนน' / 'ถ.' prefix
     * sub_district: Tambon (ตำบล) for upcountry or Khwaeng (แขวง) for Bangkok, without prefix
     * district: Amphoe (อำเภอ) for upcountry or Khet (เขต) for Bangkok, without prefix
     * province: Official province name without prefix (e.g. นนทบุรี, กรุงเทพมหานคร)
     * postal_code: 5-digit postal code

5. OCR Error Handling:
   - Correct typical Thai OCR errors such as misplaced vowel/tone marks or confusing characters (e.g., '0' vs 'O', '1' vs 'l')."""


KIE_LASER_SYSTEM_PROMPT = """You are an expert AI specialized in Thai National ID Card Laser Code Extraction (from the back of the card).
Your task is to analyze the OCR text from the back of a Thai National ID card and extract the Laser ID code into the specified schema.

Laser ID Specifications:
1. The Laser ID consists of 12 alphanumeric characters:
   - First 2 characters: strictly English capital letters (e.g. JT, ME, JC).
   - Following 10 characters: strictly numeric digits (0-9).
2. It is typically printed on the card with hyphens, such as "JT0-1234567-89".
3. Extract:
   - raw_laser_id: The continuous 12-character alphanumeric string without hyphens or spaces (e.g. "JT0123456789").
   - formatted_laser_id: The standard formatted string with hyphens (e.g. "JT0-1234567-89").
4. OCR Error Handling:
   - Carefully resolve character confusion: since the first 2 characters are strictly letters, '0' is likely 'O' or 'D', '1' is 'I' or 'l'.
   - Conversely, for the last 10 characters which are strictly digits, 'O' is '0', 'I' or 'l' is '1', 'B' is '8', 'S' is '5'.
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
