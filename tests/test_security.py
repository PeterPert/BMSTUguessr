"""Tests for app.security — password hashing, validation, and verification."""

from __future__ import annotations

from app.security import (
    hash_password,
    validate_password,
    validate_username,
    verify_password,
)


class TestValidateUsername:
    """Tests for validate_username()."""

    def test_valid_latin(self):
        ok, _ = validate_username("player_one")
        assert ok is True

    def test_valid_cyrillic(self):
        ok, _ = validate_username("Игрок-1")
        assert ok is True

    def test_valid_min_length(self):
        ok, _ = validate_username("abc")
        assert ok is True

    def test_too_short(self):
        ok, msg = validate_username("ab")
        assert ok is False
        assert msg  # error message present

    def test_too_long(self):
        ok, _ = validate_username("a" * 25)
        assert ok is False

    def test_rejects_spaces(self):
        ok, _ = validate_username("has space")
        assert ok is False

    def test_rejects_special_chars(self):
        ok, _ = validate_username("user@name!")
        assert ok is False

    def test_strips_whitespace(self):
        ok, _ = validate_username("  player  ")
        assert ok is True


class TestValidatePassword:
    """Tests for validate_password()."""

    def test_valid_password(self):
        ok, _ = validate_password("MyPass12")
        assert ok is True

    def test_too_short(self):
        ok, msg = validate_password("Ab1")
        assert ok is False
        assert "8" in msg

    def test_no_letters(self):
        ok, msg = validate_password("12345678")
        assert ok is False
        assert "букв" in msg

    def test_no_digits(self):
        ok, msg = validate_password("NoDigitsHere")
        assert ok is False
        assert "цифр" in msg

    def test_exactly_8_chars(self):
        ok, _ = validate_password("Abcdefg1")
        assert ok is True


class TestHashAndVerify:
    """Tests for hash_password() + verify_password() round-trip."""

    def test_correct_password_verifies(self):
        pw = "TestPass123"
        hashed, salt = hash_password(pw)
        assert verify_password(pw, hashed, salt) is True

    def test_wrong_password_rejected(self):
        hashed, salt = hash_password("CorrectPass1")
        assert verify_password("WrongPass1", hashed, salt) is False

    def test_unique_salts(self):
        """Each call to hash_password produces a different salt."""
        _, salt1 = hash_password("SamePassword1")
        _, salt2 = hash_password("SamePassword1")
        assert salt1 != salt2

    def test_unique_hashes(self):
        """Different salts → different hashes even for the same password."""
        hash1, _ = hash_password("SamePassword1")
        hash2, _ = hash_password("SamePassword1")
        assert hash1 != hash2

    def test_hash_is_base64_string(self):
        hashed, salt = hash_password("AnyPassword1")
        assert isinstance(hashed, str)
        assert isinstance(salt, str)
        assert len(hashed) > 0
        assert len(salt) > 0
