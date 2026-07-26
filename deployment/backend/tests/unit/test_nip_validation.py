"""
Unit tests for NIP checksum validation (RAO-P2-003).
"""
import pytest
from contractors.service import validate_nip_checksum


class TestNIPChecksum:
    """Test cases for NIP checksum validation."""

    def test_valid_nip(self):
        """Test valid NIP numbers."""
        # Generate valid NIPs using the algorithm
        # First 9 digits: 123456789
        # Weights: [6, 5, 7, 2, 3, 4, 5, 6, 7]
        # Sum: 1*6 + 2*5 + 3*7 + 4*2 + 5*3 + 6*4 + 7*5 + 8*6 + 9*7 = 6+10+21+8+15+24+35+48+63 = 230
        # Checksum: 230 % 11 = 10
        # Last digit should be 10, but NIP uses 0 for 10
        # So valid NIP: 1234567890

        # Another example: 111111111
        # Sum: 1*6 + 1*5 + 1*7 + 1*2 + 1*3 + 1*4 + 1*5 + 1*6 + 1*7 = 6+5+7+2+3+4+5+6+7 = 45
        # Checksum: 45 % 11 = 1
        # Valid NIP: 1111111111

        # Another: 222222222
        # Sum: 2*45 = 90
        # Checksum: 90 % 11 = 2
        # Valid NIP: 2222222222

        valid_nips = [
            "1234567890",  # Generated valid NIP
            "1111111111",  # Generated valid NIP
            "2222222222",  # Generated valid NIP
        ]
        for nip in valid_nips:
            assert validate_nip_checksum(nip), f"NIP {nip} should be valid"

    def test_nip_with_spaces_and_hyphens(self):
        """Test NIP with spaces and hyphens."""
        assert validate_nip_checksum("123-456-78-90"), "NIP with hyphens should be valid"
        assert validate_nip_checksum("123 456 78 90"), "NIP with spaces should be valid"

    def test_invalid_nip_checksum(self):
        """Test NIP with invalid checksum."""
        invalid_nips = [
            "1234567891",  # Wrong checksum (last digit should be 0)
            "1234567899",  # Wrong checksum
            "0000000001",  # Wrong checksum
        ]
        for nip in invalid_nips:
            assert not validate_nip_checksum(nip), f"NIP {nip} should be invalid"

    def test_invalid_nip_length(self):
        """Test NIP with invalid length."""
        invalid_lengths = [
            "123456789",   # 9 digits
            "12345678901", # 11 digits
            "12345",       # 5 digits
        ]
        for nip in invalid_lengths:
            assert not validate_nip_checksum(nip), f"NIP {nip} with invalid length should be invalid"

    def test_nip_with_letters(self):
        """Test NIP with letters."""
        assert not validate_nip_checksum("123456789a"), "NIP with letters should be invalid"
        assert not validate_nip_checksum("abcdefghij"), "NIP with only letters should be invalid"

    def test_empty_nip(self):
        """Test empty NIP."""
        assert not validate_nip_checksum(""), "Empty NIP should be invalid"
        assert not validate_nip_checksum(None), "None NIP should be invalid"

    def test_nip_with_special_chars(self):
        """Test NIP with special characters."""
        assert not validate_nip_checksum("123@456789"), "NIP with special chars should be invalid"