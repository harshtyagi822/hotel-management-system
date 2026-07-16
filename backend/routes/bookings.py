from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from flask import Blueprint, jsonify, request
from sqlalchemy import and_, asc
from sqlalchemy.exc import IntegrityError

from database import db
from models.booking import Booking
from models.room import Room
from utils.validators import validate_email, validate_phone

bookings_bp = Blueprint("bookings", __name__, url_prefix="/api/bookings")

BOOKING_STATUSES = {"Pending", "Confirmed", "Checked In", "Checked Out", "Cancelled"}
PAYMENT_STATUSES = {"Pending", "Paid", "Refunded"}
ROOM_BLOCKED_STATUSES = {"Maintenance", "Booked"}


def _json_error(message: str, status_code: int = 400, *, validation_errors: dict[str, Any] | None = None):
    payload: dict[str, Any] = {"success": False, "message": message}
    if validation_errors is not None:
        payload["validation_errors"] = validation_errors
    resp = jsonify(payload)
    resp.status_code = status_code
    return resp


def _booking_to_dict(b: Booking) -> dict[str, Any]:
    return {
        "id": b.id,
        "booking_number": b.booking_number,
        "customer_name": b.customer_name,
        "customer_email": b.customer_email,
        "customer_phone": b.customer_phone,
        "room_id": b.room_id,
        "check_in_date": b.check_in_date.isoformat() if b.check_in_date else None,
        "check_out_date": b.check_out_date.isoformat() if b.check_out_date else None,
        "adults": b.adults,
        "children": b.children,
        "total_amount": b.total_amount,
        "booking_status": b.booking_status,
        "payment_status": b.payment_status,
        "special_request": b.special_request,
        "created_at": b.created_at.isoformat() if b.created_at else None,
        "updated_at": b.updated_at.isoformat() if b.updated_at else None,
    }


def _parse_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip())
        except ValueError:
            return None
    return None


def _generate_booking_number() -> str:
    # BK + YYYY + MM + 3-digit sequence from DB count-like heuristic.
    # Uniqueness is enforced by the database; IntegrityError will be handled.
    now = datetime.utcnow()
    prefix = f"BK{now.year}{now.month:02d}"
    # Use latest booking_number matching prefix when available, otherwise start at 1.
    latest = (
        Booking.query.filter(Booking.booking_number.like(f"{prefix}%"))
        .order_by(Booking.booking_number.desc())
        .first()
    )
    seq = 1
    if latest and latest.booking_number and len(latest.booking_number) >= len(prefix) + 3:
        try:
            seq = int(latest.booking_number[-3:]) + 1
        except Exception:
            seq = 1
    return f"{prefix}{seq:03d}"


def _apply_room_status_for_booking_change(*, room: Room, new_booking_status: str):
    if new_booking_status in {"Checked Out", "Cancelled"}:
        room.status = "Available"
    # When booking is created it will already be set externally to Booked.
    elif new_booking_status in {"Pending", "Confirmed", "Checked In"}:
        # Keep room booked while active.
        room.status = "Booked"


def _validate_booking_payload(payload: dict[str, Any], *, partial: bool = False) -> tuple[bool, dict[str, Any] | None, dict[str, Any] | None]:
    cleaned: dict[str, Any] = {}
    validation_errors: dict[str, Any] = {}

    def req(field: str):
        if field not in payload or payload.get(field) in (None, ""):
            validation_errors[field] = "This field is required"

    required_fields = [
        "customer_name",
        "customer_email",
        "customer_phone",
        "room_id",
        "check_in_date",
        "check_out_date",
        "adults",
        "children",
        "total_amount",
        "booking_status",
        "payment_status",
    ]

    if not partial:
        for f in required_fields:
            if f not in payload or payload.get(f) in (None, ""):
                validation_errors[f] = "This field is required"

    # Optional
    if "special_request" in payload:
        sr = payload.get("special_request")
        cleaned["special_request"] = sr.strip() if isinstance(sr, str) else sr

    # customer_name
    if "customer_name" in payload or not partial:
        v = payload.get("customer_name")
        if v is None and not partial:
            pass
        else:
            if not isinstance(v, str) or not v.strip():
                validation_errors["customer_name"] = "customer_name must be a non-empty string"
            else:
                cleaned["customer_name"] = v.strip()

    # customer_email
    if "customer_email" in payload or not partial:
        v = payload.get("customer_email")
        ve = validate_email(v) if (isinstance(v, str) or v is None) else None
        if ve is None and not partial:
            validation_errors["customer_email"] = "customer_email is invalid"
        elif ve is not None:
            cleaned["customer_email"] = ve

    # customer_phone
    if "customer_phone" in payload:
        vp = validate_phone(payload.get("customer_phone"))
        if vp is None:
            validation_errors["customer_phone"] = "customer_phone is invalid"
        else:
            cleaned["customer_phone"] = vp

    # room_id
    if "room_id" in payload or not partial:
        try:
            rid = int(payload.get("room_id"))
            if rid <= 0:
                raise ValueError
            cleaned["room_id"] = rid
        except Exception:
            if not partial:
                validation_errors["room_id"] = "room_id must be a positive integer"

    # dates
    if "check_in_date" in payload or not partial:
        ci = _parse_date(payload.get("check_in_date"))
        if ci is None:
            validation_errors["check_in_date"] = "check_in_date must be a valid ISO date (YYYY-MM-DD)"
        else:
            cleaned["check_in_date"] = ci

    if "check_out_date" in payload or not partial:
        co = _parse_date(payload.get("check_out_date"))
        if co is None:
            validation_errors["check_out_date"] = "check_out_date must be a valid ISO date (YYYY-MM-DD)"
        else:
            cleaned["check_out_date"] = co

    # Validate date relationship when both present
    if "check_in_date" in cleaned and "check_out_date" in cleaned:
        if cleaned["check_out_date"] <= cleaned["check_in_date"]:
            validation_errors["check_out_date"] = "check_out_date must be greater than check_in_date"

    # adults/children
    if "adults" in payload or not partial:
        try:
            a = int(payload.get("adults"))
            if a < 1:
                raise ValueError
            cleaned["adults"] = a
        except Exception:
            validation_errors["adults"] = "adults must be an integer >= 1"

    if "children" in payload or not partial:
        try:
            c = int(payload.get("children"))
            if c < 0:
                raise ValueError
            cleaned["children"] = c
        except Exception:
            validation_errors["children"] = "children must be an integer >= 0"

    # total_amount
    if "total_amount" in payload or not partial:
        try:
            ta = float(payload.get("total_amount"))
            if ta <= 0:
                raise ValueError
            cleaned["total_amount"] = ta
        except Exception:
            validation_errors["total_amount"] = "total_amount must be a number > 0"

    # booking_status/payment_status
    if "booking_status" in payload or not partial:
        bs = payload.get("booking_status")
        if not isinstance(bs, str) or bs.strip() not in BOOKING_STATUSES:
            validation_errors["booking_status"] = f"booking_status must be one of: {', '.join(sorted(BOOKING_STATUSES))}"
        else:
            cleaned["booking_status"] = bs.strip()

    if "payment_status" in payload or not partial:
        ps = payload.get("payment_status")
        if not isinstance(ps, str) or ps.strip() not in PAYMENT_STATUSES:
            validation_errors["payment_status"] = f"payment_status must be one of: {', '.join(sorted(PAYMENT_STATUSES))}"
        else:
            cleaned["payment_status"] = ps.strip()

    # If partial update and nothing valid supplied
    if partial and not cleaned and not validation_errors:
        return True, {}, None

    if validation_errors:
        return False, None, validation_errors
    return True, cleaned, None


def _ensure_room_available(room: Room):
    if room.status in ROOM_BLOCKED_STATUSES:
        raise ValueError(f"Room is not available (status: {room.status})")


@bookings_bp.get("")
def get_bookings():
    query = Booking.query

    status = request.args.get("status")
    payment_status = request.args.get("payment_status")
    customer_email = request.args.get("customer_email")
    room_id = request.args.get("room_id")

    if status:
        query = query.filter(Booking.booking_status == status.strip())
    if payment_status:
        query = query.filter(Booking.payment_status == payment_status.strip())
    if customer_email:
        query = query.filter(Booking.customer_email == customer_email.strip())
    if room_id:
        try:
            rid = int(room_id)
            query = query.filter(Booking.room_id == rid)
        except ValueError:
            return _json_error("room_id must be an integer", 400)

    sort = (request.args.get("sort") or "").strip()
    if sort == "check_in_date":
        query = query.order_by(asc(Booking.check_in_date))
    elif sort == "created_at":
        query = query.order_by(asc(Booking.created_at))

    bookings = query.all()
    return jsonify({"success": True, "data": [_booking_to_dict(b) for b in bookings]})


@bookings_bp.get("/<int:booking_id>")
def get_booking(booking_id: int):
    booking = Booking.query.get(booking_id)
    if not booking:
        return _json_error("Booking not found", 404)
    return jsonify({"success": True, "data": _booking_to_dict(booking)})


@bookings_bp.post("")
def create_booking():
    payload = request.get_json(silent=True) or {}

    ok, cleaned, validation_errors = _validate_booking_payload(payload, partial=False)
    if not ok or cleaned is None:
        return _json_error("Validation failed", 400, validation_errors=validation_errors)

    room = Room.query.get(cleaned["room_id"])
    if not room:
        return _json_error("Room not found", 404)

    try:
        _ensure_room_available(room)
    except ValueError as e:
        return _json_error(str(e), 409)

    booking_number = _generate_booking_number()

    booking = Booking(
        booking_number=booking_number,
        customer_name=cleaned["customer_name"],
        customer_email=cleaned["customer_email"],
        customer_phone=cleaned.get("customer_phone"),
        room_id=cleaned["room_id"],
        check_in_date=cleaned["check_in_date"],
        check_out_date=cleaned["check_out_date"],
        adults=cleaned["adults"],
        children=cleaned["children"],
        total_amount=cleaned["total_amount"],
        booking_status=cleaned["booking_status"],
        payment_status=cleaned["payment_status"],
        special_request=cleaned.get("special_request"),
    )

    # Business rule: when booking created, update room status Available -> Booked
    room.status = "Booked"

    try:
        db.session.add(booking)
        db.session.add(room)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _json_error("Booking number conflict", 409)
    except Exception:
        db.session.rollback()
        return _json_error("Failed to create booking", 500)

    return jsonify({"success": True, "data": _booking_to_dict(booking)}), 201


@bookings_bp.put("/<int:booking_id>")
def update_booking(booking_id: int):
    booking = Booking.query.get(booking_id)
    if not booking:
        return _json_error("Booking not found", 404)

    payload = request.get_json(silent=True) or {}
    ok, cleaned, validation_errors = _validate_booking_payload(payload, partial=True)
    if not ok or cleaned is None:
        return _json_error("Validation failed", 400, validation_errors=validation_errors)

    if not cleaned:
        return _json_error("No valid fields provided to update", 400)

    old_booking_status = booking.booking_status
    old_room_id = booking.room_id

    # If room_id is changing, enforce room rules.
    new_room_id = cleaned.get("room_id", old_room_id)
    if "room_id" in cleaned and new_room_id != old_room_id:
        room = Room.query.get(new_room_id)
        if not room:
            return _json_error("Room not found", 404)
        try:
            _ensure_room_available(room)
        except ValueError as e:
            return _json_error(str(e), 409)

    for key, value in cleaned.items():
        setattr(booking, key, value)

    # Apply business rules for room status transitions on status change.
    new_status = booking.booking_status
    if new_status != old_booking_status:
        room = Room.query.get(booking.room_id)
        if room:
            _apply_room_status_for_booking_change(room=room, new_booking_status=new_status)

    # If we changed dates, enforce rule (already validated when fields present).
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _json_error("Update conflict", 409)
    except Exception:
        db.session.rollback()
        return _json_error("Failed to update booking", 500)

    return jsonify({"success": True, "data": _booking_to_dict(booking)})


@bookings_bp.delete("/<int:booking_id>")
def delete_booking(booking_id: int):
    booking = Booking.query.get(booking_id)
    if not booking:
        return _json_error("Booking not found", 404)

    # Business rule: if cancelled via delete, free the room.
    room = Room.query.get(booking.room_id)
    try:
        if room:
            room.status = "Available"
        db.session.delete(booking)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _json_error("Failed to delete booking", 409)
    except Exception:
        db.session.rollback()
        return _json_error("Failed to delete booking", 500)

    return jsonify({"success": True, "message": "Booking deleted"})


