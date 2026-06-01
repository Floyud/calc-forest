"""OCR service using RapidOCR for handwritten math answer recognition.

Initializes the OCR engine once at startup (singleton) and provides
functions to recognize handwritten numbers and math expressions from
photos taken with phone cameras.
"""
from __future__ import annotations

import io
import logging
import re
from dataclasses import dataclass, field

import cv2
import numpy as np
from rapidocr import RapidOCR

logger = logging.getLogger(__name__)

_engine: RapidOCR | None = None


@dataclass
class OCRResult:
    """Structured OCR output."""
    text: str = ""
    confidence: float = 0.0
    boxes: list[list[list[int]]] = field(default_factory=list)
    all_texts: list[str] = field(default_factory=list)
    raw_result: object = None


def init_ocr_engine() -> None:
    """Initialize the RapidOCR engine (call once at startup)."""
    global _engine
    if _engine is not None:
        return
    logger.info("Initializing RapidOCR engine...")
    _engine = RapidOCR()
    logger.info("RapidOCR engine ready.")


def get_ocr_engine() -> RapidOCR:
    """Get the shared OCR engine instance."""
    if _engine is None:
        init_ocr_engine()
    assert _engine is not None
    return _engine




_OCR_CHAR_MAP: dict[str, str] = {
    "O": "0", "o": "0",
    "l": "1", "I": "1",
    "S": "5", "s": "5",
    "Z": "2",
    "g": "9",
    "B": "8",
    "×": "×", "x": "×", "X": "×",
    "÷": "÷",
    "+": "+",
    "-": "-",
    "=": "=",
    ".": ".",
    "/": "/",
    "：": ":",
    "：": ":",
}

_ALLOWED_CHARS = set("0123456789+-×÷=./")

_MATH_EXPR_RE = re.compile(r"[\d+\-×÷=./\s]+")


def _clean_math_text(raw: str) -> str:
    """Post-process OCR text to clean up common recognition errors for math."""
    cleaned = []
    for ch in raw.strip():
        mapped = _OCR_CHAR_MAP.get(ch, ch)
        if mapped in _ALLOWED_CHARS:
            cleaned.append(mapped)
    result = "".join(cleaned).strip()
    # Remove trailing operators that are likely artifacts
    result = result.rstrip("+-×÷=.")
    return result


def _preprocess_image(image_bytes: bytes) -> np.ndarray:
    """Preprocess image for better OCR on handwritten digits.

    Steps: decode → grayscale → threshold (binarize) → optional resize.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("无法解码图片")

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Adaptive threshold for handwritten text (handles varying lighting)
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 10
    )

    return binary


def recognize_math_answer(image_bytes: bytes) -> OCRResult:
    """Recognize a handwritten math answer from an image.

    Optimized for single-line answers: numbers, fractions, simple expressions.
    The answer is typically a number like "1023" or "3/4" written on paper.

    Returns OCRResult with the cleaned text and confidence score.
    """
    engine = get_ocr_engine()

    # Preprocess
    try:
        processed = _preprocess_image(image_bytes)
    except ValueError:
        return OCRResult(text="", confidence=0.0)

    # Run OCR with lower thresholds for handwritten text
    result = engine(
        processed,
        text_score=0.3,
        box_thresh=0.3,
        use_det=True,
        use_cls=True,
        use_rec=True,
    )

    if result.txts is None or len(result.txts) == 0:
        return OCRResult(text="", confidence=0.0)

    # Collect all recognized text fragments, sort by x-coordinate (left to right)
    texts_with_boxes = []
    for i, txt in enumerate(result.txts):
        box = result.boxes[i] if result.boxes is not None and i < len(result.boxes) else None
        x_pos = box[0][0] if box is not None else 0
        texts_with_boxes.append((x_pos, txt))

    texts_with_boxes.sort(key=lambda t: t[0])

    # Join all text fragments
    raw_text = "".join(t[1] for t in texts_with_boxes)

    # Clean for math
    cleaned = _clean_math_text(raw_text)

    # Average confidence
    scores = result.scores if result.scores else (0.0,)
    avg_conf = sum(scores) / len(scores) if scores else 0.0

    return OCRResult(
        text=cleaned,
        confidence=round(avg_conf, 3),
        boxes=[b.tolist() if hasattr(b, "tolist") else b for b in result.boxes] if result.boxes is not None else [],
        all_texts=[t[1] for t in texts_with_boxes],
        raw_result=result,
    )


def recognize_work_image(image_bytes: bytes) -> OCRResult:
    """Recognize a full 'show your work' image (calculation steps).

    Less aggressive cleaning — keeps all text for teacher review.
    """
    engine = get_ocr_engine()

    try:
        processed = _preprocess_image(image_bytes)
    except ValueError:
        return OCRResult(text="", confidence=0.0)

    result = engine(processed, text_score=0.3, box_thresh=0.3)

    if result.txts is None or len(result.txts) == 0:
        return OCRResult(text="", confidence=0.0)

    # Sort by position: top-to-bottom, then left-to-right
    texts_with_pos = []
    for i, txt in enumerate(result.txts):
        box = result.boxes[i] if result.boxes is not None and i < len(result.boxes) else None
        if box is not None:
            y_pos = (box[0][1] + box[2][1]) / 2
            x_pos = box[0][0]
        else:
            y_pos, x_pos = 0, 0
        texts_with_pos.append((y_pos, x_pos, txt))

    texts_with_pos.sort(key=lambda t: (t[0], t[1]))

    full_text = "\n".join(t[2] for t in texts_with_pos)
    scores = result.scores if result.scores else (0.0,)
    avg_conf = sum(scores) / len(scores) if scores else 0.0

    return OCRResult(
        text=full_text,
        confidence=round(avg_conf, 3),
        boxes=[b.tolist() if hasattr(b, "tolist") else b for b in result.boxes] if result.boxes is not None else [],
        all_texts=[t[2] for t in texts_with_pos],
        raw_result=result,
    )
