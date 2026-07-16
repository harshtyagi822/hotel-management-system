from __future__ import annotations

from datetime import datetime, date
from typing import Any, Optional

from flask import Blueprint, jsonify
from sqlalchemy import case, func

from database import db
from models.booking import Booking
from models.customer import Customer
from models.payment import Payment
from models.room import Room

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


def _json_error(message: str, status_code: int = 400):
    resp = jsonify({"success": False, "message": message})
    resp.status_code = status_code
    return resp


def _parse_today() -> date:
    return datetime.utcnow().date()


def _safe_div(n: float, d: float) -> float:
    try:
        if d == 0:
            return 0
        return float(n) / float(d)
    except Exception:
        return 0


@dashboard_bp.get("/summary")
def dashboard_summary():
    today = _parse_today()

    rooms = db.session.query(Room).subquery()

    total_rooms = db.session.query(func.count(Room.id)).scalar() or 0
    available_rooms = db.session.query(func.count(Room.id)).filter(Room.status == "Available").scalar() or 0
    booked_rooms = db.session.query(func.count(Room.id)).filter(Room.status == "Booked").scalar() or 0
    maintenance_rooms = db.session.query(func.count(Room.id)).filter(Room.status == "Maintenance").scalar() or 0

    total_bookings = db.session.query(func.count(Booking.id)).scalar() or 0
    pending_bookings = db.session.query(func.count(Booking.id)).filter(Booking.booking_status == "Pending").scalar() or 0
    confirmed_bookings = db.session.query(func.count(Booking.id)).filter(Booking.booking_status == "Confirmed").scalar() or 0
    checked_in = db.session.query(func.count(Booking.id)).filter(Booking.booking_status == "Checked In").scalar() or 0
    checked_out = db.session.query(func.count(Booking.id)).filter(Booking.booking_status == "Checked Out").scalar() or 0
    cancelled_bookings = db.session.query(func.count(Booking.id)).filter(Booking.booking_status == "Cancelled").scalar() or 0

    total_customers = db.session.query(func.count(Customer.id)).scalar() or 0

    today_checkins = db.session.query(func.count(Booking.id)).filter(Booking.check_in_date == today).scalar() or 0
    today_checkouts = db.session.query(func.count(Booking.id)).filter(Booking.check_out_date == today).scalar() or 0

    paid_filter = Payment.payment_status == "Paid"

    today_revenue = (
        db.session.query(func.coalesce(func.sum(Payment.amount), 0.0))
        .filter(paid_filter)
        .filter(Payment.payment_date == today)
        .scalar()
        or 0
    )

    monthly_revenue = 0
    yearly_revenue = 0
    try:
        now = datetime.utcnow()
        monthly_revenue = (
            db.session.query(func.coalesce(func.sum(Payment.amount), 0.0))
            .filter(paid_filter)
            .filter(func.extract("year", Payment.payment_date) == now.year)
            .filter(func.extract("month", Payment.payment_date) == now.month)
            .scalar()
            or 0
        )
        yearly_revenue = (
            db.session.query(func.coalesce(func.sum(Payment.amount), 0.0))
            .filter(paid_filter)
            .filter(func.extract("year", Payment.payment_date) == now.year)
            .scalar()
            or 0
        )
    except Exception:
        # If extract() isn't supported by the underlying dialect, keep 0s.
        pass

    occupancy_rate = _safe_div(booked_rooms + (total_rooms - total_rooms), total_rooms)
    # The above keeps it simple; true occupancy needs room-date spans.
    # For now, treat booked rooms as occupied.
    occupancy_rate = _safe_div(booked_rooms, total_rooms)

    return jsonify(
        {
            "success": True,
            "data": {
                "total_rooms": total_rooms,
                "available_rooms": available_rooms,
                "booked_rooms": booked_rooms,
                "maintenance_rooms": maintenance_rooms,
                "total_bookings": total_bookings,
                "pending_bookings": pending_bookings,
                "confirmed_bookings": confirmed_bookings,
                "checked_in": checked_in,
                "checked_out": checked_out,
                "cancelled_bookings": cancelled_bookings,
                "total_customers": total_customers,
                "today_checkins": today_checkins,
                "today_checkouts": today_checkouts,
                "today_revenue": float(today_revenue),
                "monthly_revenue": float(monthly_revenue),
                "yearly_revenue": float(yearly_revenue),
                "occupancy_rate": occupancy_rate,
            },
        }
    )


@dashboard_bp.get("/recent-bookings")
def recent_bookings():
    bookings = Booking.query.order_by(Booking.created_at.desc()).limit(10).all()
    data = [
        {
            "id": b.id,
            "booking_number": b.booking_number,
            "customer_name": b.customer_name,
            "customer_email": b.customer_email,
            "room_id": b.room_id,
            "check_in_date": b.check_in_date.isoformat() if b.check_in_date else None,
            "check_out_date": b.check_out_date.isoformat() if b.check_out_date else None,
            "booking_status": b.booking_status,
            "payment_status": b.payment_status,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        }
        for b in bookings
    ]
    return jsonify({"success": True, "data": data})


@dashboard_bp.get("/recent-payments")
def recent_payments():
    payments = Payment.query.order_by(Payment.created_at.desc()).limit(10).all()
    data = [_payment_to_dict(p) for p in payments]
    return jsonify({"success": True, "data": data})


def _payment_to_dict(p: Payment) -> dict[str, Any]:
    return {
        "id": p.id,
        "payment_number": p.payment_number,
        "invoice_number": p.invoice_number,
        "booking_id": p.booking_id,
        "customer_name": p.customer_name,
        "customer_email": p.customer_email,
        "amount": p.amount,
        "payment_method": p.payment_method,
        "payment_status": p.payment_status,
        "transaction_id": p.transaction_id,
        "payment_date": p.payment_date.isoformat() if p.payment_date else None,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


@dashboard_bp.get("/monthly-revenue")
def monthly_revenue():
    # Group by month using SQLAlchemy ORM functions. Returns list of {month, revenue}.
    now = datetime.utcnow()

    rows = (
        db.session.query(
            func.date_format(Payment.payment_date, "%Y-%m").label("month"),
            func.coalesce(func.sum(Payment.amount), 0.0).label("revenue"),
        )
        .filter(Payment.payment_status == "Paid")
        .group_by(func.date_format(Payment.payment_date, "%Y-%m"))
        .order_by("month")
        .limit(12)
        .all()
    )

    data = [{"month": r.month, "revenue": float(r.revenue)} for r in rows]
    return jsonify({"success": True, "data": data})


@dashboard_bp.get("/room-occupancy")
def room_occupancy():
    available = db.session.query(func.count(Room.id)).filter(Room.status == "Available").scalar() or 0
    booked = db.session.query(func.count(Room.id)).filter(Room.status == "Booked").scalar() or 0
    maintenance = db.session.query(func.count(Room.id)).filter(Room.status == "Maintenance").scalar() or 0
    return jsonify({"success": True, "data": {"Available": available, "Booked": booked, "Maintenance": maintenance}})


@dashboard_bp.get("/booking-status")
def booking_status():
    return jsonify(
        {
            "success": True,
            "data": {
                "Pending": db.session.query(func.count(Booking.id)).filter(Booking.booking_status == "Pending").scalar() or 0,
                "Confirmed": db.session.query(func.count(Booking.id)).filter(Booking.booking_status == "Confirmed").scalar() or 0,
                "Checked In": db.session.query(func.count(Booking.id)).filter(Booking.booking_status == "Checked In").scalar() or 0,
                "Checked Out": db.session.query(func.count(Booking.id)).filter(Booking.booking_status == "Checked Out").scalar() or 0,
                "Cancelled": db.session.query(func.count(Booking.id)).filter(Booking.booking_status == "Cancelled").scalar() or 0,
            },
        }
    )


@dashboard_bp.get("/payment-status")
def payment_status():
    return jsonify(
        {
            "success": True,
            "data": {
                "Pending": db.session.query(func.count(Payment.id)).filter(Payment.payment_status == "Pending").scalar() or 0,
                "Paid": db.session.query(func.count(Payment.id)).filter(Payment.payment_status == "Paid").scalar() or 0,
                "Failed": db.session.query(func.count(Payment.id)).filter(Payment.payment_status == "Failed").scalar() or 0,
                "Refunded": db.session.query(func.count(Payment.id)).filter(Payment.payment_status == "Refunded").scalar() or 0,
            },
        }
    )


@dashboard_bp.get("/ping")
def dashboard_ping():
    return jsonify({"success": True, "message": "Dashboard subsystem ready"})


