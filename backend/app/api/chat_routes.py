import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.report import Report
from app.models.user import User
from app.rag.chat_service import answer_question
from app.schemas.chat_schema import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = db.execute(
        select(Report).where(Report.id == payload.report_id, Report.user_id == current_user.id)
    ).scalar_one_or_none()

    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    try:
        answer, sources = answer_question(
            db, current_user, report, payload.message, payload.search_all_reports
        )
    except Exception:
        logger.exception("Chat failed for user %s, report %s", current_user.id, report.id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI assistant is unavailable right now. Please try again.",
        )

    return ChatResponse(answer=answer, sources=sources)
