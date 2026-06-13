"""
GridFS storage helpers.

All file binaries (images / PDFs) are stored in the 'medical_files' GridFS
bucket. Document metadata (filename, hospital, folder, OCR status …) lives
in the 'documents' collection.
"""

import io
import os
from pathlib import Path

from bson import ObjectId

from backend.database import documents_col, fs_bucket

# MIME type → extension mapping (only accepted formats)
ALLOWED_MIME_TYPES: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "application/pdf": ".pdf",
}

VALID_FOLDERS = {"prescriptions", "reports"}


async def generate_unique_stored_filename(
    original_filename: str,
    hospital_id: str,
    folder: str,
) -> str:
    """
    Return a filename that does not yet exist in the same hospital+folder.
    If 'report.pdf' exists, tries 'report_1.pdf', 'report_2.pdf', … until free.
    """
    base = Path(original_filename).stem
    ext = Path(original_filename).suffix.lower()
    candidate = f"{base}{ext}"
    counter = 0

    while True:
        exists = await documents_col.find_one(
            {
                "hospital_id": hospital_id,
                "folder": folder,
                "stored_filename": candidate,
            }
        )
        if not exists:
            return candidate
        counter += 1
        candidate = f"{base}_{counter}{ext}"


async def save_file_to_gridfs(
    content: bytes,
    stored_filename: str,
    mime_type: str,
    hospital_id: str,
    folder: str,
) -> ObjectId:
    """Upload bytes to GridFS and return the GridFS file_id."""
    file_id: ObjectId = await fs_bucket.upload_from_stream(
        stored_filename,
        io.BytesIO(content),
        metadata={
            "hospital_id": hospital_id,
            "folder": folder,
            "content_type": mime_type,
        },
    )
    return file_id


async def stream_file_from_gridfs(file_id: str):
    """
    Yield chunks of a file stored in GridFS.
    Used by the preview / download endpoint as an async generator.
    """
    grid_out = await fs_bucket.open_download_stream(ObjectId(file_id))
    while True:
        chunk = await grid_out.read(65536)  # 64 KB chunks
        if not chunk:
            break
        yield chunk


async def read_file_bytes_from_gridfs(file_id: str) -> bytes:
    """Download an entire file from GridFS into memory. Use for OCR worker."""
    grid_out = await fs_bucket.open_download_stream(ObjectId(file_id))
    return await grid_out.read()


async def delete_file_from_gridfs(file_id: str) -> None:
    """Delete a file from GridFS by its file_id string."""
    await fs_bucket.delete(ObjectId(file_id))
