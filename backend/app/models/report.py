from datetime import datetime, date, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    report_name: Mapped[str] = mapped_column(String(255))
    report_date: Mapped[date] = mapped_column(Date)
    upload_date: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    file_url: Mapped[str] = mapped_column(String(500))
    raw_text: Mapped[Optional[str]] = mapped_column(default=None)

    user: Mapped["User"] = relationship(back_populates="reports")
    biomarkers: Mapped[list["Biomarker"]] = relationship(back_populates="report", cascade="all, delete-orphan")