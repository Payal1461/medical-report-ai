from datetime import datetime, timezone
from sqlalchemy import String, DateTime, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("firebase_uid", name="uq_users_firebase_uid"),
        CheckConstraint(
            "password_hash IS NOT NULL OR firebase_uid IS NOT NULL",
            name="ck_users_has_authentication",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    firebase_uid: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    reports: Mapped[list["Report"]] = relationship(back_populates="user", cascade="all, delete-orphan")
