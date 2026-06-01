"""Common utility functions for services."""
import hashlib
import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_PASSWORD_SALT = os.getenv("PASSWORD_SALT", "calc-forest-2026")


def hash_password(password: str) -> str:
    salted = f"{_PASSWORD_SALT}:{password}".encode()
    return hashlib.sha256(salted).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed


def json_column(row, key: str, default=None):
    raw = row[key]
    if raw is None:
        return default if default is not None else []
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        logger.warning("Failed to parse JSON column '%s': %s", key, raw)
        return default if default is not None else []


def validate_json_list(value: Any, field_name: str) -> list:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
    logger.warning("Invalid JSON list for field '%s': %s", field_name, value)
    return []


def validate_json_dict(value: Any, field_name: str) -> dict:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
    logger.warning("Invalid JSON dict for field '%s': %s", field_name, value)
    return {}


def placeholders(count: int) -> str:
    return ",".join(["?"] * count)
