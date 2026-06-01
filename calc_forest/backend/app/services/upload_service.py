"""Image upload service for student camera photos."""
from __future__ import annotations

import logging
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

UPLOAD_ROOT = Path(__file__).resolve().parent.parent.parent / "data" / "uploads"

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@dataclass
class UploadResult:
    file_id: str
    path: str
    url: str
    size: int


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


async def save_upload(
    student_id: str,
    image_bytes: bytes,
    filename: str,
    homework_id: str | None = None,
) -> UploadResult:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"文件类型 {ext} 不允许。允许的类型: {ALLOWED_EXTENSIONS}")

    if len(image_bytes) > MAX_FILE_SIZE:
        raise ValueError(f"文件过大: {len(image_bytes)} bytes (max {MAX_FILE_SIZE})")

    date_str = time.strftime("%Y-%m-%d")
    subdir = UPLOAD_ROOT / student_id / date_str
    _ensure_dir(subdir)

    file_id = uuid.uuid4().hex[:8]
    safe_name = f"{int(time.time())}_{file_id}{ext}"
    file_path = subdir / safe_name

    with open(file_path, "wb") as f:
        f.write(image_bytes)

    url = f"/static/uploads/{student_id}/{date_str}/{safe_name}"
    return UploadResult(file_id=file_id, path=str(file_path), url=url, size=len(image_bytes))
