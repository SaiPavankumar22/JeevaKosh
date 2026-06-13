"""
Hospital routes.

POST   /hospitals                → create a hospital (auto-provisions prescriptions & reports folders)
GET    /hospitals                → list all hospitals with document counts
GET    /hospitals/{hospital_id}  → get one hospital
DELETE /hospitals/{hospital_id}  → delete hospital (and all its documents + files)
"""

import re
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException

from backend.database import documents_col, hospitals_col
from backend.models.hospital import HospitalCreate, HospitalResponse
from backend.services.storage import delete_file_from_gridfs

router = APIRouter(prefix="/hospitals", tags=["Hospitals"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _parse_object_id(raw: str) -> ObjectId:
    try:
        return ObjectId(raw)
    except (InvalidId, Exception):
        raise HTTPException(status_code=400, detail=f"Invalid id: {raw}")


async def _build_response(hospital: dict) -> HospitalResponse:
    hosp_id = str(hospital["_id"])
    total_prescriptions = await documents_col.count_documents(
        {"hospital_id": hosp_id, "folder": "prescriptions"}
    )
    total_reports = await documents_col.count_documents(
        {"hospital_id": hosp_id, "folder": "reports"}
    )
    return HospitalResponse(
        id=hosp_id,
        name=hospital["name"],
        slug=hospital["slug"],
        created_at=hospital["created_at"],
        total_prescriptions=total_prescriptions,
        total_reports=total_reports,
    )


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/", response_model=HospitalResponse, status_code=201)
async def create_hospital(data: HospitalCreate):
    """
    Create a new hospital. The two logical sub-folders (prescriptions, reports)
    are provisioned automatically — no explicit folder creation is needed.
    """
    slug = _slugify(data.name)
    if await hospitals_col.find_one({"slug": slug}):
        raise HTTPException(
            status_code=409,
            detail=f"A hospital named '{data.name}' already exists.",
        )

    doc = {
        "name": data.name.strip(),
        "slug": slug,
        "created_at": datetime.now(timezone.utc),
    }
    result = await hospitals_col.insert_one(doc)
    doc["_id"] = result.inserted_id
    return await _build_response(doc)


@router.get("/", response_model=list[HospitalResponse])
async def list_hospitals():
    """Return all hospitals sorted by creation date (newest first)."""
    hospitals = await hospitals_col.find().sort("created_at", -1).to_list(None)
    return [await _build_response(h) for h in hospitals]


@router.get("/{hospital_id}", response_model=HospitalResponse)
async def get_hospital(hospital_id: str):
    """Return a single hospital by its id."""
    oid = _parse_object_id(hospital_id)
    hospital = await hospitals_col.find_one({"_id": oid})
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found.")
    return await _build_response(hospital)


@router.delete("/{hospital_id}", status_code=200)
async def delete_hospital(hospital_id: str):
    """
    Delete a hospital and cascade-delete all its documents (metadata + GridFS files).
    """
    oid = _parse_object_id(hospital_id)
    if not await hospitals_col.find_one({"_id": oid}):
        raise HTTPException(status_code=404, detail="Hospital not found.")

    # Delete all GridFS files belonging to this hospital
    docs = await documents_col.find({"hospital_id": hospital_id}).to_list(None)
    for doc in docs:
        try:
            await delete_file_from_gridfs(str(doc["file_id"]))
        except Exception:
            pass  # already gone; continue cleanup

    await documents_col.delete_many({"hospital_id": hospital_id})
    await hospitals_col.delete_one({"_id": oid})

    return {"message": f"Hospital '{hospital_id}' and all its records deleted."}
