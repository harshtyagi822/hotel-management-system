"""Request validation utilities."""

from __future__ import annotations

import re
from typing import Optional


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_RE = re.compile(r"^[0-9+\-\s()]{7,25}$")


def normalize_str(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return value.strip()


def validate_email(email: Optional[str]) -> Optional[str]:
    email = normalize_str(email)
    if not email:
        return None
    if not _EMAIL_RE.match(email):
        return None
    return email


def validate_phone(phone: Optional[str]) -> Optional[str]:
    phone = normalize_str(phone)
    if not phone:
        return None
    if not _PHONE_RE.match(phone):
        return None
    return phone


def validate_password(password: Optional[str]) -> bool:
    password = password or ""
    return len(password) >= 8

