from pydantic import BaseModel, Field
from datetime import datetime


class HospitalCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200, description="Hospital name")


class HospitalResponse(BaseModel):
    id: str
    name: str
    slug: str
    created_at: datetime
    total_prescriptions: int = 0
    total_reports: int = 0
