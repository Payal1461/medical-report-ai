from sqlalchemy import String, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.session import Base


class BiomarkerStatus(str, enum.Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"


class Biomarker(Base):
    __tablename__ = "biomarkers"

    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"))
    name: Mapped[str] = mapped_column(String(100))
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(50))
    ref_low: Mapped[float] = mapped_column(Float)
    ref_high: Mapped[float] = mapped_column(Float)
    status: Mapped[BiomarkerStatus] = mapped_column(SQLEnum(BiomarkerStatus))

    report: Mapped["Report"] = relationship(back_populates="biomarkers")