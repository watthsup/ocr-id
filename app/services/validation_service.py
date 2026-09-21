"""Validation service for Thai National ID card domain checks."""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class ValidationService:
    """Provides algorithmic verification for Thai National ID card domain rules."""

    @staticmethod
    def validate_thai_id_checksum(id_number: Optional[str]) -> bool:
        """Validates the 13-digit Thai National ID checksum using Modulo 11 arithmetic.

        Algorithm:
            Sum = sum(d[i] * (13 - i)) for i in range(12)
            Remainder = Sum % 11
            Check Digit = (11 - Remainder) % 10
            Valid if Check Digit == d[12]
        """
        if not id_number:
            return False

        clean_id = "".join(c for c in str(id_number) if c.isdigit())
        if len(clean_id) != 13:
            return False

        digits = [int(c) for c in clean_id]
        total_sum = sum(digits[i] * (13 - i) for i in range(12))
        remainder = total_sum % 11
        check_digit = (11 - remainder) % 10

        return check_digit == digits[12]

    @staticmethod
    def validate_laser_id_format(laser_id: Optional[str]) -> bool:
        """Validates Thai ID Laser Code format (back of card).

        Standard pattern: 2 English uppercase letters followed by 10 digits (12 characters total).
        Display format: XX0-0000000-00 (e.g. JT0-1234567-89).
        """
        if not laser_id:
            return False

        clean = re.sub(r"[^A-Za-z0-9]", "", str(laser_id)).upper()
        return bool(re.match(r"^[A-Z]{2}\d{10}$", clean))

    @staticmethod
    def format_laser_id(laser_id: Optional[str]) -> Optional[str]:
        """Formats a 12-char laser ID into standard XX0-0000000-00 format."""
        if not laser_id:
            return None

        clean = re.sub(r"[^A-Za-z0-9]", "", str(laser_id)).upper()
        if len(clean) == 12 and re.match(r"^[A-Z]{2}\d{10}$", clean):
            return f"{clean[:3]}-{clean[3:10]}-{clean[10:12]}"
        return laser_id
