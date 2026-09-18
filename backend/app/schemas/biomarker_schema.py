from typing import Optional
from pydantic import BaseModel
from app.models.biomarker import BiomarkerStatus


class BiomarkerOut(BaseModel):
    id: int
    name: str
    value: float
    unit: str
    ref_low: float
    ref_high: float
    status: BiomarkerStatus
    explanation: Optional[str] = None

    class Config:
        from_attributes = True