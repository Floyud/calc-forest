"""Shared FastAPI dependencies and helpers."""

from __future__ import annotations

from fastapi import HTTPException


def _check_service_result(result):
    """Raise 404 if service returned an error dict, otherwise pass through."""
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result
