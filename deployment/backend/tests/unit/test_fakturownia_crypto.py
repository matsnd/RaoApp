"""Unit tests for backend/integrations/fakturownia/crypto.py — RAO-P2-012 QA."""
import pytest
from cryptography.fernet import Fernet

from integrations.fakturownia.crypto import (
    encrypt_token,
    decrypt_token,
    mask_token,
)


# Generated fresh per test session — never used in production
TEST_KEY = Fernet.generate_key().decode()


# ── encrypt/decrypt roundtrip ────────────────────────────────────────────────

def test_encrypt_decrypt_roundtrip():
    plain = "tk_secret_1234567890abcdef"
    cipher = encrypt_token(plain, key=TEST_KEY)
    assert isinstance(cipher, bytes)
    assert plain.encode() not in cipher  # not just plaintext
    assert decrypt_token(cipher, key=TEST_KEY) == plain


def test_encrypt_decrypt_polish_chars():
    plain = "tk_ąćęłńóśźż_ĄĆĘŁŃÓŚŹŻ"
    cipher = encrypt_token(plain, key=TEST_KEY)
    assert decrypt_token(cipher, key=TEST_KEY) == plain


def test_encrypt_decrypt_emoji():
    plain = "token_🚜📋_emoji"
    cipher = encrypt_token(plain, key=TEST_KEY)
    assert decrypt_token(cipher, key=TEST_KEY) == plain


def test_encrypt_produces_different_ciphertexts():
    """Fernet uses random IV — same plaintext encrypts to different ciphertexts."""
    plain = "tk_same_value"
    c1 = encrypt_token(plain, key=TEST_KEY)
    c2 = encrypt_token(plain, key=TEST_KEY)
    assert c1 != c2
    assert decrypt_token(c1, key=TEST_KEY) == plain
    assert decrypt_token(c2, key=TEST_KEY) == plain


def test_encrypt_empty_raises():
    with pytest.raises(ValueError, match="empty"):
        encrypt_token("", key=TEST_KEY)


def test_decrypt_empty_raises():
    with pytest.raises(ValueError, match="empty"):
        decrypt_token(b"", key=TEST_KEY)


def test_decrypt_wrong_key_raises():
    plain = "tk_secret"
    cipher = encrypt_token(plain, key=TEST_KEY)
    other_key = Fernet.generate_key().decode()
    with pytest.raises(ValueError, match="Invalid ciphertext"):
        decrypt_token(cipher, key=other_key)


def test_decrypt_tampered_ciphertext_raises():
    plain = "tk_secret"
    cipher = encrypt_token(plain, key=TEST_KEY)
    tampered = cipher[:-4] + b"XXXX"
    with pytest.raises(ValueError):
        decrypt_token(tampered, key=TEST_KEY)


# ── mask_token ───────────────────────────────────────────────────────────────

def test_mask_token_standard():
    """Token >= 8 chars: pierwsze 4 + **** + ostatnie 4."""
    assert mask_token("tk_secret_1234567890") == "tk_s****7890"


def test_mask_token_exactly_8():
    """Edge case: exactly 8 chars → still first4 + last4 (overlap visually but per impl)."""
    assert mask_token("12345678") == "1234****5678"


def test_mask_short_token_under_8():
    """Token < 8 chars: fallback to asterisks (no leakage of partial token)."""
    result = mask_token("short")  # len 5
    # Per impl: "****" * min(4, len(plain)//2) → "****" * 2 = "********"
    assert result == "********"
    # Critical: nothing from original plain leaks
    assert "s" not in result
    assert "short" not in result


def test_mask_token_empty():
    assert mask_token("") == "****"


def test_mask_token_single_char():
    """Edge: len=1 → //2 = 0 → "****" * 0 = ""."""
    assert mask_token("x") == ""


def test_mask_token_two_chars():
    """len=2 → //2 = 1 → "****" * 1 = "****"."""
    assert mask_token("ab") == "****"


def test_mask_token_polish_chars():
    """Polish chars don't crash masking (no encoding issues)."""
    plain = "ąćęłtokenąćęł"  # >= 8 chars
    result = mask_token(plain)
    assert "****" in result
    assert result.startswith(plain[:4])
    assert result.endswith(plain[-4:])
