from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database import db


class Booking(db.Model):  # type: ignore[misc]
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    booking_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)

    customer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    customer_email: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    customer_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)

    room_id: Mapped[int] = mapped_column(Integer, ForeignKey("rooms.id"), nullable=False, index=True)

    check_in_date: Mapped[date] = mapped_column(Date, nullable=False)
    check_out_date: Mapped[date] = mapped_column(Date, nullable=False)

    adults: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    children: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    total_amount: Mapped[float] = mapped_column(Float(asdecimal=False), nullable=False)

    booking_status: Mapped[str] = mapped_column(String(30), nullable=False, default="Pending", index=True)
    payment_status: Mapped[str] = mapped_column(String(30), nullable=False, default="Pending", index=True)

    special_request: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


