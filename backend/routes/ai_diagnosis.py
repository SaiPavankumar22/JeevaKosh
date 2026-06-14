"""
AI Diagnosis routes — voice interview session, STT/TTS, and MedGemma analysis.
All endpoints are prefixed with /ai-diagnosis.
Authentication is NOT required so the interview is accessible without a JWT.
"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.medgemma_service import analyze_symptoms
from backend.services.sarvam_service import text_to_speech, transcribe_audio
from backend.services.session_store import store

router = APIRouter(prefix="/ai-diagnosis", tags=["AI Diagnosis"])

# ── Red-flag keywords ──────────────────────────────────────────────────────────
_RED_FLAGS = [
    "difficulty breathing", "chest pain", "coughing blood", "vomiting blood",
    "sudden confusion", "weakness on one side", "faint", "unconscious",
    "severe chest", "can't breathe", "shortness of breath",
    "hemoptysis", "hematemesis", "stroke", "emergency",
]


def _has_red_flag(text: str) -> bool:
    low = text.lower()
    return any(kw in low for kw in _RED_FLAGS)


# ── Schemas ────────────────────────────────────────────────────────────────────

class SessionStartRequest(BaseModel):
    preferred_language: str = "en"


class SessionStartResponse(BaseModel):
    session_id: str
    first_question: str
    audio_base64: str
    language: str


class TranscribeRequest(BaseModel):
    session_id: str
    audio_base64: str
    language: str
    mime_type: str = "audio/webm"


class TranscribeResponse(BaseModel):
    transcript: str
    session_id: str


class SpeakRequest(BaseModel):
    text: str
    language: str


class SpeakResponse(BaseModel):
    audio_base64: str


class AnswerSubmitRequest(BaseModel):
    session_id: str
    question_key: str
    answer: str


class AnswerSubmitResponse(BaseModel):
    next_question: Optional[str] = None
    audio_base64: Optional[str] = None
    is_complete: bool
    question_number: int
    is_emergency: bool = False


class Differential(BaseModel):
    condition_name: str
    brief_reason: str
    confidence: str


class DiagnosisRequest(BaseModel):
    session_id: str


class DiagnosisResponse(BaseModel):
    urgency: str
    clinical_summary: str
    urgency_reason: str
    care_timeline: str
    red_flags_detected: List[str] = []
    differentials: List[Differential]
    next_steps: List[str]
    when_to_seek_care: str
    reassuring_notes: str = ""
    disclaimer: str
    answers: dict = {}


# ── Session ────────────────────────────────────────────────────────────────────

@router.post("/session/start", response_model=SessionStartResponse)
async def start_session(request: SessionStartRequest):
    """Create a new diagnostic session and return the first question with TTS audio."""
    try:
        session = store.create_session(request.preferred_language)
        first_question = session.get_current_question_text()
        audio_base64 = await text_to_speech(first_question, session.language)
        return SessionStartResponse(
            session_id=session.session_id,
            first_question=first_question,
            audio_base64=audio_base64,
            language=session.language,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


# ── Voice ──────────────────────────────────────────────────────────────────────

@router.post("/voice/transcribe", response_model=TranscribeResponse)
async def transcribe(request: TranscribeRequest):
    """Transcribe a base64-encoded audio recording using Sarvam STT."""
    try:
        transcript = await transcribe_audio(
            request.audio_base64, request.language, request.mime_type
        )
        return TranscribeResponse(transcript=transcript, session_id=request.session_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/voice/speak", response_model=SpeakResponse)
async def speak(request: SpeakRequest):
    """Convert text to speech using Sarvam TTS."""
    try:
        audio = await text_to_speech(request.text, request.language)
        return SpeakResponse(audio_base64=audio)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/voice/answer", response_model=AnswerSubmitResponse)
async def submit_answer(request: AnswerSubmitRequest):
    """
    Save an answer to the current question.
    Advances to the next question (with TTS audio) or marks the session complete.
    """
    session = store.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    store.save_answer(request.session_id, request.question_key, request.answer)

    is_emergency = False
    if request.question_key == "red_flag_screen" and _has_red_flag(request.answer):
        is_emergency = True
        store.mark_emergency(request.session_id)

    is_complete = session.is_complete()
    resp = AnswerSubmitResponse(
        is_complete=is_complete,
        is_emergency=is_emergency,
        question_number=session.current_question_index + 1,
    )

    if not is_complete:
        next_text = store.advance_question(request.session_id)
        if next_text:
            try:
                audio = await text_to_speech(next_text, session.language)
                resp.next_question = next_text
                resp.audio_base64 = audio
            except Exception:
                resp.next_question = next_text
    else:
        store.complete_session(request.session_id)

    return resp


# ── Diagnosis ──────────────────────────────────────────────────────────────────

@router.post("/diagnosis/analyze", response_model=DiagnosisResponse)
async def get_diagnosis(request: DiagnosisRequest):
    """Run MedGemma analysis on collected answers and return differential diagnosis."""
    session = store.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session.answers:
        raise HTTPException(status_code=400, detail="No answers collected yet")

    try:
        result = await analyze_symptoms(session.answers, session.language)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    if session.status == "emergency":
        result["urgency"] = "emergency"
        if not result.get("red_flags_detected"):
            result["red_flags_detected"] = ["Potential emergency symptoms reported during screening"]

    result["answers"] = session.answers
    return DiagnosisResponse(**result)
