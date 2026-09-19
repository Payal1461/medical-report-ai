from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.report import Report
from app.models.biomarker import Biomarker
from app.schemas.trend_schema import BiomarkerTrend, BiomarkerHistoryPoint
from app.services.explanation_service import summarize_trend

router = APIRouter(tags=["trends"])


@router.get("/trends/{biomarker_name}", response_model=BiomarkerTrend)
def get_biomarker_trend(
    biomarker_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    results = db.execute(
        select(Biomarker, Report)
        .join(Report, Biomarker.report_id == Report.id)
        .where(Report.user_id == current_user.id, Biomarker.name == biomarker_name)
        .order_by(Report.report_date.asc())
    ).all()

    if not results:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No history found for this biomarker")

    history = [
        BiomarkerHistoryPoint(
            report_id=report.id,
            report_date=report.report_date,
            value=biomarker.value,
            status=biomarker.status.value,
        )
        for biomarker, report in results
    ]

    trend_summary = None
    if len(history) >= 2:
        trend_summary = summarize_trend(
            biomarker_name,
            [{"report_date": str(h.report_date), "value": h.value, "status": h.status} for h in history],
        )

    return BiomarkerTrend(
        name=biomarker_name,
        unit=results[0][0].unit,
        history=history,
        trend_summary=trend_summary,
    )