from datetime import datetime, date
from pydantic import BaseModel


class ReportOut(BaseModel):
    id: int
    report_name: str
    report_date: date
    upload_date: datetime
    file_url: str

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    message: str
    report: ReportOut