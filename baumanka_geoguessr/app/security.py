from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re

PBKDF2_ITERATIONS = 240_000
USERNAME_RE = re.compile(r"^[A-Za-zА-Яа-яЁё0-9_\-]{3,24}$")


def validate_username(username: str) -> tuple[bool, str]:
    username = username.strip()
    if not USERNAME_RE.match(username):
        return False, "Никнейм: 3-24 символа, буквы/цифры/_/- без пробелов."
    return True, ""


def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Пароль должен быть не короче 8 символов."
    if not any(ch.isalpha() for ch in password):
        return False, "В пароле должна быть хотя бы одна буква."
    if not any(ch.isdigit() for ch in password):
        return False, "В пароле должна быть хотя бы одна цифра."
    return True, ""


def hash_password(password: str) -> tuple[str, str]:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return (
        base64.b64encode(digest).decode("ascii"),
        base64.b64encode(salt).decode("ascii"),
    )


def verify_password(password: str, stored_hash: str, stored_salt: str) -> bool:
    salt = base64.b64decode(stored_salt.encode("ascii"))
    expected = base64.b64decode(stored_hash.encode("ascii"))
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return hmac.compare_digest(digest, expected)
