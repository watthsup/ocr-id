"""Unit tests for Thai ID checksum and Laser ID validation."""

import pytest
from app.services.validation_service import ValidationService


def test_thai_id_checksum_valid():
    # 1 1007 01234 56 1 -> Sum = 165, 165 % 11 = 0, Check digit = 1
    assert ValidationService.validate_thai_id_checksum("1100701234561") is True
    assert ValidationService.validate_thai_id_checksum("1-1007-01234-56-1") is True

    # 1 2345 67890 12 1 -> Sum = 352, 352 % 11 = 0, Check digit = 1
    assert ValidationService.validate_thai_id_checksum("1234567890121") is True


def test_thai_id_checksum_invalid():
    # Wrong check digit
    assert ValidationService.validate_thai_id_checksum("1100701234560") is False
    assert ValidationService.validate_thai_id_checksum("1234567890129") is False

    # Corrupted lengths or types
    assert ValidationService.validate_thai_id_checksum("1234567890") is False
    assert ValidationService.validate_thai_id_checksum("123456789012345") is False
    assert ValidationService.validate_thai_id_checksum("") is False
    assert ValidationService.validate_thai_id_checksum(None) is False
    assert ValidationService.validate_thai_id_checksum("abcdefghijklm") is False


def test_laser_id_format_valid():
    # 2 letters + 10 digits
    assert ValidationService.validate_laser_id_format("JT0123456789") is True
    assert ValidationService.validate_laser_id_format("JT0-1234567-89") is True
    assert ValidationService.validate_laser_id_format("me0-9876543-21") is True


def test_laser_id_format_invalid():
    # Only digits, or wrong letter count
    assert ValidationService.validate_laser_id_format("123456789012") is False
    assert ValidationService.validate_laser_id_format("JTA123456789") is False
    assert ValidationService.validate_laser_id_format("J01234567891") is False
    assert ValidationService.validate_laser_id_format("JT012345") is False
    assert ValidationService.validate_laser_id_format("") is False
    assert ValidationService.validate_laser_id_format(None) is False


def test_laser_id_formatting():
    assert ValidationService.format_laser_id("JT0123456789") == "JT0-1234567-89"
    assert ValidationService.format_laser_id("JT0-1234567-89") == "JT0-1234567-89"
