from __future__ import annotations

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database import db


class Employee(db.Model):  # type: ignore[misc]
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    full_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(180), unique=True, nullable=False, index=True)

    # Optional phone for search/validation parity with Customer/User
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)

    # HR fields requested by Phase 2
    department: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    designation: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)

    # Salary: keep as float to match existing backend patterns
    salary: Mapped[float] = mapped_column(Float(asdecimal=False), nullable=False, default=0.0)

    # Employment status
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active", index=True)

    # Role field (separate from JWT role)
    role: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)

