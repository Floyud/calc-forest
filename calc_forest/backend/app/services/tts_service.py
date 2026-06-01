"""Text-to-speech service using edge-tts (Microsoft Edge TTS)."""

from __future__ import annotations

import edge_tts

# Chinese voices
DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"
AVAILABLE_VOICES = [
    "zh-CN-XiaoxiaoNeural",   # Female, warm
    "zh-CN-YunxiNeural",      # Male, calm
    "zh-CN-XiaoyiNeural",     # Female, gentle
    "zh-CN-YunjianNeural",    # Male, confident
]


async def generate_tts(text: str, voice: str | None = None) -> bytes:
    """Generate TTS audio from text, return MP3 bytes.

    Args:
        text: The Chinese text to synthesize.
        voice: Voice name. Defaults to zh-CN-XiaoxiaoNeural.

    Returns:
        MP3 audio bytes.

    Raises:
        ValueError: If text is empty or voice is unsupported.
        RuntimeError: If edge-tts fails to produce audio.
    """
    if not text or not text.strip():
        raise ValueError("文本不能为空")

    voice = voice or DEFAULT_VOICE

    communicate = edge_tts.Communicate(text, voice)
    chunks: list[bytes] = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            chunks.append(chunk["data"])

    if not chunks:
        raise RuntimeError("语音合成未产生音频数据")

    return b"".join(chunks)
