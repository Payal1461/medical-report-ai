from typing import Optional
from pydantic import BaseModel
from app.schemas.biomarker_schema import BiomarkerOut


class DashboardSummary(BaseModel):
    normal_count: int
    low_count: int
    high_count: int
    total_count: int


class DashboardOut(BaseModel):
    report_id: int
    report_name: str
    summary: DashboardSummary
    biomarkers: list[BiomarkerOut]
    overall_summary: Optional[str] = None