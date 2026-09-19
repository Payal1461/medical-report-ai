from datetime import date
from typing import Optional
from pydantic import BaseModel


class BiomarkerHistoryPoint(BaseModel):
    report_id: int
    report_date: date
    value: float
    status: str


class BiomarkerTrend(BaseModel):
    name: str
    unit: str
    history: list[BiomarkerHistoryPoint]
    trend_summary: Optional[str] = None