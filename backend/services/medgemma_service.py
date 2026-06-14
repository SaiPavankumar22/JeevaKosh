"""
MedGemma service — clinical differential diagnosis via HuggingFace OpenAI-compatible endpoint.
"""
import json
import os
import re
from typing import Any, Dict

from openai import OpenAI

from backend.voice_agent_prompts import MEDGEMMA_SYSTEM_PROMPT

HF_INFERENCE_ENDPOINT: str = os.getenv("HF_INFERENCE_ENDPOINT", "")
HF_API_TOKEN: str = os.getenv("HF_API_TOKEN", "")
HF_MODEL: str = os.getenv("HF_MODEL", "google/medgemma-4b-it")

# Ensure endpoint ends with /v1
if HF_INFERENCE_ENDPOINT and not HF_INFERENCE_ENDPOINT.rstrip("/").endswith("/v1"):
    HF_INFERENCE_ENDPOINT = HF_INFERENCE_ENDPOINT.rstrip("/") + "/v1"


def _client() -> OpenAI:
    if not HF_API_TOKEN or not HF_INFERENCE_ENDPOINT:
        raise ValueError("HF_API_TOKEN or HF_INFERENCE_ENDPOINT is not set")
    return OpenAI(base_url=HF_INFERENCE_ENDPOINT, api_key=HF_API_TOKEN)


async def analyze_symptoms(answers: Dict[str, str], language: str) -> Dict[str, Any]:
    """Send collected symptom answers to MedGemma and return a structured diagnosis."""
    user_message = "Patient symptom interview answers:\n" + json.dumps(answers, indent=2)

    try:
        response = _client().chat.completions.create(
            model=HF_MODEL,
            messages=[
                {"role": "system", "content": MEDGEMMA_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.2,
            max_tokens=1024,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or ""
        return _validate(_extract_json(raw))
    except Exception as exc:
        raise Exception(f"MedGemma analysis error: {exc}") from exc


def _extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Could not parse JSON from model output: {text[:300]}")


def _normalize_urgency(value: str) -> str:
    mapping = {
        "emergency": "emergency",
        "urgent": "urgent",
        "routine": "routine",
        "monitor": "monitor",
        "low": "monitor",
        "medium": "routine",
        "high": "urgent",
        "critical": "emergency",
    }
    return mapping.get((value or "routine").strip().lower(), "routine")


def _validate(data: Dict[str, Any]) -> Dict[str, Any]:
    validated_diffs = []
    for d in data.get("differentials", []):
        if isinstance(d, dict):
            validated_diffs.append({
                "condition_name": d.get("condition_name", "Unknown"),
                "brief_reason": d.get("brief_reason", ""),
                "confidence": d.get("confidence", "possible"),
            })
        elif isinstance(d, str) and d.strip():
            validated_diffs.append({"condition_name": d.strip(), "brief_reason": "", "confidence": "possible"})

    next_steps = data.get("next_steps", [])
    if not isinstance(next_steps, list):
        next_steps = []

    urgency = _normalize_urgency(data.get("urgency", "routine"))
    care_timeline = data.get("care_timeline") or _default_care_timeline(urgency)

    red_flags = data.get("red_flags_detected", [])
    if not isinstance(red_flags, list):
        red_flags = []
    red_flags = [str(f).strip() for f in red_flags if str(f).strip()]

    return {
        "urgency": urgency,
        "clinical_summary": data.get("clinical_summary") or _default_summary(validated_diffs, urgency),
        "urgency_reason": data.get("urgency_reason") or _default_urgency_reason(urgency),
        "care_timeline": care_timeline,
        "red_flags_detected": red_flags,
        "differentials": validated_diffs,
        "next_steps": [str(s) for s in next_steps],
        "when_to_seek_care": data.get("when_to_seek_care") or "Seek emergency care immediately if symptoms worsen.",
        "reassuring_notes": data.get("reassuring_notes") or "",
        "disclaimer": data.get("disclaimer") or (
            "This is an AI-generated preliminary assessment based on your reported symptoms. "
            "It is not a medical diagnosis. Please consult a qualified doctor for proper evaluation."
        ),
    }


def _default_care_timeline(urgency: str) -> str:
    return {
        "emergency": "Immediately",
        "urgent": "Within 24 hours",
        "routine": "This week",
        "monitor": "Monitor at home",
    }.get(urgency, "This week")


def _default_urgency_reason(urgency: str) -> str:
    return {
        "emergency": "Your reported symptoms may indicate a serious condition that needs immediate medical attention.",
        "urgent": "Your symptoms suggest you should be evaluated by a doctor soon.",
        "routine": "Your symptoms appear manageable but should be reviewed by a healthcare provider.",
        "monitor": "Your symptoms may improve with rest and self-care, but watch for any worsening.",
    }.get(urgency, "Please follow the recommended next steps below.")


def _default_summary(differentials: list, urgency: str) -> str:
    if not differentials:
        return "Based on your answers, we have generated a preliminary assessment of your symptoms."
    top = differentials[0]["condition_name"]
    return (
        f"Based on your symptom interview, the most relevant possibility is {top}. "
        f"This assessment is rated as {urgency} priority."
    )
