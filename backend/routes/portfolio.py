"""
Portfolio sharing — generate a PDF, store in Supabase, issue timed access.

Authenticated endpoints:
  POST   /portfolio/generate       → create a new share (returns link + QR code)
  GET    /portfolio/my             → list the user's active shares
  DELETE /portfolio/{token}        → revoke a share early
  GET    /portfolio/documents/all  → list all user documents (for selection UI)

Public endpoint (no auth required):
  GET    /portfolio/view/{token}   → validates token, streams the PDF directly
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from backend.database import documents_col, portfolios_col, profiles_col
from backend.services.auth import get_current_user
from backend.services.pdf_generator import generate_portfolio_pdf
from backend.services.qr_service import generate_qr_base64
from backend.services import supabase_service
from backend.services.storage import read_file_bytes_from_gridfs

import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000").rstrip("/")

EXPIRY_OPTIONS: dict[int, str] = {
    1:   "1 hour",
    6:   "6 hours",
    24:  "24 hours",
    72:  "3 days",
    168: "7 days",
    720: "30 days",
}


# ── Schemas ───────────────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    document_ids: list[str] = Field(default_factory=list)
    expires_in_hours: int = Field(24, ge=1, le=720)
    title: Optional[str] = Field(None, max_length=120)


class ShareInfo(BaseModel):
    token: str
    title: Optional[str]
    share_url: str
    qr_code_base64: str
    expires_at: datetime
    expires_label: str
    document_count: int
    created_at: datetime


class ShareListItem(BaseModel):
    token: str
    title: Optional[str]
    share_url: str
    expires_at: datetime
    expires_label: str
    document_count: int
    created_at: datetime
    is_expired: bool
    is_revoked: bool


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_oid(raw: str) -> ObjectId:
    try:
        return ObjectId(raw)
    except (InvalidId, Exception):
        raise HTTPException(status_code=400, detail=f"Invalid document id: {raw}")


def _expires_label(hours: int) -> str:
    return EXPIRY_OPTIONS.get(hours, f"{hours} hours")


def _share_url(token: str) -> str:
    return f"{BACKEND_BASE_URL}/portfolio/view/{token}"


def _is_expired(doc: dict) -> bool:
    exp = doc.get("expires_at")
    if exp is None:
        return False
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) > exp


def _doc_to_list_item(doc: dict) -> ShareListItem:
    token = doc["token"]
    return ShareListItem(
        token=token,
        title=doc.get("title"),
        share_url=_share_url(token),
        expires_at=doc["expires_at"],
        expires_label=doc.get("expires_label", ""),
        document_count=len(doc.get("document_ids", [])),
        created_at=doc["created_at"],
        is_expired=_is_expired(doc),
        is_revoked=doc.get("is_revoked", False),
    )


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/documents/all", tags=["Portfolio"])
async def list_all_user_documents(current_user: dict = Depends(get_current_user)):
    """Return all documents belonging to the current user (for selection UI)."""
    user_id = str(current_user["_id"])
    docs = (
        await documents_col.find({"user_id": user_id})
        .sort([("folder", 1), ("hospital_name", 1), ("upload_date", -1)])
        .to_list(None)
    )
    return [
        {
            "id": str(d["_id"]),
            "hospital_name": d.get("hospital_name", ""),
            "folder": d.get("folder", ""),
            "original_filename": d.get("original_filename", ""),
            "upload_date": d.get("upload_date"),
            "ocr_status": d.get("ocr_status", ""),
            "mime_type": d.get("mime_type", ""),
            "file_size": d.get("file_size", 0),
        }
        for d in docs
    ]


@router.post("/generate", response_model=ShareInfo, status_code=201)
async def generate_share(
    body: GenerateRequest,
    current_user: dict = Depends(get_current_user),
):
    user_id = str(current_user["_id"])

    # 1. Fetch profile
    profile_doc = await profiles_col.find_one({"user_id": user_id})
    if not profile_doc:
        raise HTTPException(
            status_code=404,
            detail="Profile not found. Please fill in your profile before sharing.",
        )

    # 2. Fetch selected documents + read their file bytes from GridFS
    selected_docs_with_files: list[tuple[dict, bytes | None]] = []
    if body.document_ids:
        for doc_id in body.document_ids:
            doc = await documents_col.find_one(
                {"_id": _parse_oid(doc_id), "user_id": user_id}
            )
            if not doc:
                continue
            try:
                file_bytes = await read_file_bytes_from_gridfs(doc["file_id"])
            except Exception as exc:
                print(f"[portfolio] could not read file {doc_id}: {exc}")
                file_bytes = None
            selected_docs_with_files.append((doc, file_bytes))

    # 3. Build expiry
    expires_at = datetime.now(timezone.utc) + timedelta(hours=body.expires_in_hours)
    expires_label = _expires_label(body.expires_in_hours)
    expires_at_str = expires_at.strftime("%d %b %Y, %H:%M UTC")

    # 4. Generate PDF (with embedded file previews)
    try:
        pdf_bytes = generate_portfolio_pdf(
            profile=profile_doc,
            documents=selected_docs_with_files,
            expires_label=expires_at_str,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}")

    # 5. Upload to Supabase
    token = secrets.token_urlsafe(24)
    file_path = f"{user_id}/{token}.pdf"

    try:
        await supabase_service.ensure_bucket_exists()
        await supabase_service.upload_pdf(file_path, pdf_bytes)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Storage upload failed: {exc}")

    # 6. Store share record in MongoDB
    now = datetime.now(timezone.utc)
    share_doc = {
        "user_id": user_id,
        "token": token,
        "title": body.title,
        "supabase_path": file_path,
        "expires_at": expires_at,
        "expires_label": expires_label,
        "document_ids": [str(d["_id"]) for d, _ in selected_docs_with_files],
        "is_revoked": False,
        "created_at": now,
    }
    await portfolios_col.insert_one(share_doc)

    # 7. Generate QR code for the public share URL
    public_url = _share_url(token)
    try:
        qr_b64 = generate_qr_base64(public_url)
    except Exception as exc:
        print(f"[portfolio] QR generation failed: {exc}")
        qr_b64 = ""

    return ShareInfo(
        token=token,
        title=body.title,
        share_url=public_url,
        qr_code_base64=qr_b64,
        expires_at=expires_at,
        expires_label=expires_label,
        document_count=len(selected_docs_with_files),
        created_at=now,
    )


@router.get("/my", response_model=list[ShareListItem])
async def list_my_shares(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    shares = (
        await portfolios_col.find({"user_id": user_id})
        .sort("created_at", -1)
        .to_list(None)
    )
    return [_doc_to_list_item(s) for s in shares]


@router.delete("/{token}", status_code=200)
async def revoke_share(token: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    share = await portfolios_col.find_one({"token": token, "user_id": user_id})
    if not share:
        raise HTTPException(status_code=404, detail="Share not found.")

    await portfolios_col.update_one(
        {"token": token},
        {"$set": {"is_revoked": True}},
    )
    try:
        await supabase_service.delete_portfolio_file(share["supabase_path"])
    except Exception:
        pass

    return {"message": "Portfolio share revoked successfully."}


@router.get("/view/{token}", tags=["Portfolio Public"])
async def view_portfolio(token: str):
    """
    Public endpoint — no authentication required.
    Validates the token then streams the PDF directly from Supabase.
    """
    share = await portfolios_col.find_one({"token": token})

    if not share:
        return JSONResponse(
            status_code=404,
            content={"detail": "This portfolio link does not exist."},
        )

    if share.get("is_revoked"):
        return JSONResponse(
            status_code=410,
            content={"detail": "This portfolio link has been revoked by the patient."},
        )

    if _is_expired(share):
        return JSONResponse(
            status_code=410,
            content={
                "detail": (
                    "This portfolio link has expired. "
                    "Please ask the patient to generate a new share link."
                )
            },
        )

    # Download PDF bytes from Supabase and stream to the viewer
    try:
        pdf_bytes = await supabase_service.download_file(share["supabase_path"])
    except Exception as exc:
        return JSONResponse(
            status_code=502,
            content={"detail": f"Could not retrieve the portfolio file: {exc}"},
        )

    patient_name = "portfolio"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{patient_name}.pdf"',
            "Cache-Control": "no-store",
        },
    )
