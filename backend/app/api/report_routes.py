import shutil
import uuid
from datetime import date
from pathlib import Path

from app.models.biomarker import Biomarker, BiomarkerStatus
from app.extraction.pdf_extractor import extract_text_from_pdf
from app.extraction.biomarker_parser import parse_biomarkers

from app.models.chat_history import ChatHistory
from app.schemas.chat_history_schema import ChatHistoryOut


from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.report import Report
from app.schemas.report_schema import ReportOut, UploadResponse

router = APIRouter(tags=["reports"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload", response_model=UploadResponse)
def upload_report(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    raw_text = ""
    if file_extension.lower() == ".pdf":
        raw_text = extract_text_from_pdf(str(file_path))

    report = Report(
        user_id=current_user.id,
        report_name=file.filename,
        report_date=date.today(),
        file_url=str(file_path),
        raw_text=raw_text,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    if raw_text:
        parsed_biomarkers = parse_biomarkers(raw_text)
        for b in parsed_biomarkers:
            biomarker = Biomarker(
                report_id=report.id,
                name=b["name"],
                value=b["value"],
                unit=b["unit"],
                ref_low=b["ref_low"],
                ref_high=b["ref_high"],
                status=BiomarkerStatus(b["status"]),
            )
            db.add(biomarker)
        db.commit()

    return UploadResponse(
        message="File uploaded successfully",
        report=ReportOut.model_validate(report),
    )

@router.get("/reports", response_model=list[ReportOut])
def list_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reports = db.execute(
        select(Report).where(Report.user_id == current_user.id)
    ).scalars().all()
    return reports


@router.get("/report/{report_id}", response_model=ReportOut)
def get_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = db.execute(
        select(Report).where(Report.id == report_id, Report.user_id == current_user.id)
    ).scalar_one_or_none()

    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    return report


@router.get("/history", response_model=list[ChatHistoryOut])
def get_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    history = db.execute(
        select(ChatHistory)
        .where(ChatHistory.user_id == current_user.id)
        .order_by(ChatHistory.timestamp.desc())
    ).scalars().all()
    return history