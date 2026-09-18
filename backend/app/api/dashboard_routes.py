from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.report import Report
from app.models.biomarker import Biomarker, BiomarkerStatus
from app.schemas.dashboard_schema import DashboardOut, DashboardSummary
from app.schemas.biomarker_schema import BiomarkerOut
from app.services.explanation_service import explain_biomarker, summarize_report

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/{report_id}", response_model=DashboardOut)
def get_dashboard(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = db.execute(
        select(Report).where(Report.id == report_id, Report.user_id == current_user.id)
    ).scalar_one_or_none()

    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    biomarkers = db.execute(
        select(Biomarker).where(Biomarker.report_id == report_id)
    ).scalars().all()

    normal_count = sum(1 for b in biomarkers if b.status == BiomarkerStatus.NORMAL)
    low_count = sum(1 for b in biomarkers if b.status == BiomarkerStatus.LOW)
    high_count = sum(1 for b in biomarkers if b.status == BiomarkerStatus.HIGH)

    biomarker_outs = []
    for b in biomarkers:
        explanation = None
        if b.status != BiomarkerStatus.NORMAL:
            explanation = explain_biomarker(b.name, b.value, b.unit, b.ref_low, b.ref_high, b.status.value)
        biomarker_outs.append(
            BiomarkerOut(
                id=b.id, name=b.name, value=b.value, unit=b.unit,
                ref_low=b.ref_low, ref_high=b.ref_high, status=b.status,
                explanation=explanation,
            )
        )

    overall_summary = None
    if biomarkers:
        overall_summary = summarize_report([
            {"name": b.name, "value": b.value, "unit": b.unit, "status": b.status.value}
            for b in biomarkers
        ])

    return DashboardOut(
        report_id=report.id,
        report_name=report.report_name,
        summary=DashboardSummary(
            normal_count=normal_count,
            low_count=low_count,
            high_count=high_count,
            total_count=len(biomarkers),
        ),
        biomarkers=biomarker_outs,
        overall_summary=overall_summary,
    )