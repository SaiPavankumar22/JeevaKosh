"""
Sarvam AI service — speech-to-text and text-to-speech for AI Diagnosis.
"""
import base64
import os
from typing import Optional

import httpx

SARVAM_API_KEY: str = os.getenv("SARVAM_API_KEY", "")

LANGUAGE_CODES: dict[str, str] = {
    "en": "en-IN",
    "hi": "hi-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "kn": "kn-IN",
    "ml": "ml-IN",
    "bn": "bn-IN",
    "mr": "mr-IN",
    "gu": "gu-IN",
    "pa": "pa-IN",
    "od": "od-IN",
    "ur": "ur-IN",
}


def _lang(code: str) -> str:
    return LANGUAGE_CODES.get(code, "en-IN")


async def transcribe_audio(
    audio_base64: str,
    language: str,
    mime_type: str = "audio/webm",
) -> str:
    """Transcribe audio bytes (base64) using Sarvam speech-to-text."""
    if not SARVAM_API_KEY:
        raise ValueError("SARVAM_API_KEY is not set in environment")

    audio_bytes = base64.b64decode(audio_base64)
    lang_code = _lang(language)

    ext = "webm"
    content_type = mime_type or "audio/webm"
    if "wav" in content_type:
        ext, content_type = "wav", "audio/wav"
    elif "ogg" in content_type:
        ext, content_type = "ogg", "audio/ogg"
    elif "mp4" in content_type or "m4a" in content_type:
        ext, content_type = "m4a", "audio/mp4"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.sarvam.ai/speech-to-text",
            files={"file": (f"audio.{ext}", audio_bytes, content_type)},
            data={"language_code": lang_code, "model": "saarika:v2.5"},
            headers={"api-subscription-key": SARVAM_API_KEY},
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise Exception(
                f"Sarvam STT error {exc.response.status_code}: {exc.response.text}"
            ) from exc

        result = response.json()
        transcript = result.get("transcript", "")
        if not transcript:
            raise ValueError("No transcript in Sarvam response")
        return transcript


async def text_to_speech(text: str, language: str) -> str:
    """Convert text to speech via Sarvam TTS. Returns base64-encoded WAV."""
    if not SARVAM_API_KEY:
        raise ValueError("SARVAM_API_KEY is not set in environment")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.sarvam.ai/text-to-speech",
            json={
                "inputs": [text],
                "target_language_code": _lang(language),
                "speaker": "anushka",
                "model": "bulbul:v2",
                "enable_preprocessing": True,
            },
            headers={"api-subscription-key": SARVAM_API_KEY},
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise Exception(
                f"Sarvam TTS error {exc.response.status_code}: {exc.response.text}"
            ) from exc

        result = response.json()
        audios = result.get("audios", [])
        if not audios:
            raise ValueError("No audio in Sarvam TTS response")

        audio = audios[0]
        if not isinstance(audio, str):
            audio = base64.b64encode(audio).decode("utf-8")
        return audio
