"""
In-memory session store for AI Diagnosis voice interview sessions.
Sessions are lost on server restart — this is intentional (no PII persistence).
"""
import uuid
from datetime import datetime
from typing import Dict, Optional

from backend.voice_agent_prompts import QUESTIONS


class DiagnosisSession:
    def __init__(self, session_id: str, language: str):
        self.session_id = session_id
        self.language = language
        self.current_question_index = 0
        self.answers: Dict[str, str] = {}
        self.status = "active"  # "active" | "complete" | "emergency"
        self.created_at = datetime.utcnow()

    def get_current_question_text(self) -> Optional[str]:
        if self.current_question_index < len(QUESTIONS):
            return QUESTIONS[self.current_question_index]["script"]
        return None

    def is_complete(self) -> bool:
        return len(self.answers) >= len(QUESTIONS)

    def advance_to_next_question(self) -> Optional[str]:
        self.current_question_index += 1
        return self.get_current_question_text()


class SessionStore:
    def __init__(self):
        self._sessions: Dict[str, DiagnosisSession] = {}

    def create_session(self, language: str) -> DiagnosisSession:
        session_id = str(uuid.uuid4())
        session = DiagnosisSession(session_id, language)
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[DiagnosisSession]:
        return self._sessions.get(session_id)

    def save_answer(self, session_id: str, question_key: str, answer: str) -> None:
        session = self.get_session(session_id)
        if session:
            session.answers[question_key] = answer

    def advance_question(self, session_id: str) -> Optional[str]:
        session = self.get_session(session_id)
        if session:
            return session.advance_to_next_question()
        return None

    def complete_session(self, session_id: str) -> None:
        session = self.get_session(session_id)
        if session:
            session.status = "complete"

    def mark_emergency(self, session_id: str) -> None:
        session = self.get_session(session_id)
        if session:
            session.status = "emergency"


# Singleton store shared across the app lifetime
store = SessionStore()
