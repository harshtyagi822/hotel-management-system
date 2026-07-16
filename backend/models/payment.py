from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database import db


class Payment(db.Model):  # type: ignore[misc]
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    payment_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    booking_id: Mapped[int] = mapped_column(Integer, ForeignKey("bookings.id"), nullable=False, index=True)

    customer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    customer_email: Mapped[str] = mapped_column(String(120), nullable=False, index=True)

    amount: Mapped[float] = mapped_column(Float(asdecimal=False), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    payment_status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    transaction_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    invoice_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


