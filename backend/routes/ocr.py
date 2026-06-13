"""
OCR routes.

GET  /documents/{document_id}/ocr         → get extracted OCR data
GET  /documents/{document_id}/ocr/status  → get OCR processing status
POST /documents/{document_id}/ocr/retry   → re-trigger OCR for failed documents
"""

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, BackgroundTasks, HTTPException

from backend.database import documents_col
from backend.services.ocr_worker import run_ocr_for_document

router = APIRouter(prefix="/documents", tags=["OCR"])


def _parse_oid(raw: str) -> ObjectId:
    try:
        return ObjectId(raw)
    except (InvalidId, Exception):
        raise HTTPException(status_code=400, detail=f"Invalid id: {raw}")


@router.get("/{document_id}/ocr/status")
async def get_ocr_status(document_id: str):
    """
    Return the current OCR processing status for a document.

    Possible statuses:
      - pending     → queued, not yet started
      - processing  → OCR is running
      - completed   → extraction finished successfully
      - failed      → extraction failed (see ocr_error)
    """
    doc = await documents_col.find_one(
        {"_id": _parse_oid(document_id)},
        {"ocr_status": 1, "ocr_error": 1, "ocr_completed_at": 1},
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    return {
        "document_id": document_id,
        "ocr_status": doc["ocr_status"],
        "ocr_error": doc.get("ocr_error"),
        "ocr_completed_at": doc.get("ocr_completed_at"),
    }


@router.get("/{document_id}/ocr")
async def get_ocr_result(document_id: str):
    """
    Return the full OCR extraction result for a completed document.
    Returns 404 if the document doesn't exist and 409 if OCR is not yet done.
    """
    doc = await documents_col.find_one(
        {"_id": _parse_oid(document_id)},
        {
            "ocr_status": 1,
            "ocr_data": 1,
            "ocr_error": 1,
            "ocr_completed_at": 1,
            "stored_filename": 1,
            "folder": 1,
        },
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    status = doc["ocr_status"]

    if status == "pending":
        raise HTTPException(
            status_code=409,
            detail="OCR has not started yet. Check back shortly.",
        )
    if status == "processing":
        raise HTTPException(
            status_code=409,
            detail="OCR is currently running. Check back shortly.",
        )
    if status == "failed":
        raise HTTPException(
            status_code=422,
            detail={
                "message": "OCR extraction failed.",
                "ocr_error": doc.get("ocr_error"),
            },
        )

    return {
        "document_id": document_id,
        "stored_filename": doc.get("stored_filename"),
        "folder": doc.get("folder"),
        "ocr_status": status,
        "ocr_completed_at": doc.get("ocr_completed_at"),
        "ocr_data": doc.get("ocr_data"),
    }


@router.post("/{document_id}/ocr/retry", status_code=202)
async def retry_ocr(document_id: str, background_tasks: BackgroundTasks):
    """
    Re-queue OCR extraction for a document whose previous attempt failed.
    Only allowed when ocr_status is 'failed'.
    """
    doc = await documents_col.find_one(
        {"_id": _parse_oid(document_id)},
        {"ocr_status": 1},
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if doc["ocr_status"] not in ("failed", "pending"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot retry: OCR status is '{doc['ocr_status']}'. "
                   "Only 'failed' or 'pending' documents can be retried.",
        )

    background_tasks.add_task(run_ocr_for_document, document_id)

    return {
        "message": "OCR re-queued successfully.",
        "document_id": document_id,
        "ocr_status": "pending",
    }
