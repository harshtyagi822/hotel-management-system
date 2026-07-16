from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from flask import Blueprint, jsonify, request
from sqlalchemy import and_, asc
from sqlalchemy.exc import IntegrityError

from database import db
from models.booking import Booking
from models.payment import Payment
from utils.validators import validate_email

payments_bp = Blueprint("payments", __name__, url_prefix="/api/payments")

PAYMENT_METHODS = {
    "Cash",
    "Credit Card",
    "Debit Card",
    "UPI",
    "Net Banking",
    "Wallet",
}
PAYMENT_STATUSES = {"Pending", "Paid", "Failed", "Refunded"}


def _json_error(message: str, status_code: int = 400, *, validation_errors: dict[str, Any] | None = None):
    payload: dict[str, Any] = {"success": False, "message": message}
    if validation_errors is not None:
        payload["validation_errors"] = validation_errors
    resp = jsonify(payload)
    resp.status_code = status_code
    return resp


def _payment_to_dict(p: Payment) -> dict[str, Any]:
    return {
        "id": p.id,
        "payment_number": p.payment_number,
        "booking_id": p.booking_id,
        "customer_name": p.customer_name,
        "customer_email": p.customer_email,
        "amount": p.amount,
        "payment_method": p.payment_method,
        "payment_status": p.payment_status,
        "transaction_id": p.transaction_id,
        "payment_date": p.payment_date.isoformat() if p.payment_date else None,
        "invoice_number": p.invoice_number,
        "notes": p.notes,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
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


def _parse_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except Exception:
        return None


def _generate_sequence_number(model: Any, column: Any, prefix: str) -> int:
    latest = (
        model.query.filter(column.like(f"{prefix}%"))
        .order_by(column.desc())
        .first()
    )
    if latest is None:
        return 1
    val = getattr(latest, column.key, None)
    if not val:
        return 1
    tail = str(val)[-3:]
    try:
        return int(tail) + 1
    except Exception:
        return 1


def _generate_payment_number() -> str:
    now = datetime.utcnow()
    prefix = f"PAY{now.year}{now.month:02d}"
    seq = _generate_sequence_number(Payment, Payment.payment_number, prefix)
    return f"{prefix}{seq:03d}"


def _generate_invoice_number() -> str:
    now = datetime.utcnow()
    prefix = f"INV{now.year}{now.month:02d}"
    seq = _generate_sequence_number(Payment, Payment.invoice_number, prefix)
    return f"{prefix}{seq:03d}"


def _validate_payment_payload(payload: dict[str, Any], *, partial: bool = False):
    validation_errors: dict[str, Any] = {}
    cleaned: dict[str, Any] = {}

    required_fields = [
        "booking_id",
        "customer_name",
        "customer_email",
        "amount",
        "payment_method",
        "payment_status",
        "payment_date",
        "notes",
    ]

    # Allow notes to be null
    if not partial:
        for f in required_fields:
            if f not in payload:
                validation_errors[f] = "This field is required"

    # booking_id
    if "booking_id" in payload or not partial:
        try:
            rid = int(payload.get("booking_id"))
            if rid <= 0:
                raise ValueError
            cleaned["booking_id"] = rid
        except Exception:
            if not partial:
                validation_errors["booking_id"] = "booking_id must be a positive integer"

    # customer_name
    if "customer_name" in payload or not partial:
        v = payload.get("customer_name")
        if not isinstance(v, str) or not v.strip():
            validation_errors["customer_name"] = "customer_name must be a non-empty string"
        else:
            cleaned["customer_name"] = v.strip()

    # customer_email
    if "customer_email" in payload or not partial:
        ve = validate_email(payload.get("customer_email"))
        if ve is None:
            validation_errors["customer_email"] = "customer_email is invalid"
        else:
            cleaned["customer_email"] = ve

    # amount
    if "amount" in payload or not partial:
        fv = _parse_float(payload.get("amount"))
        if fv is None or fv <= 0:
            validation_errors["amount"] = "amount must be > 0"
        else:
            cleaned["amount"] = fv

    # payment_method
    if "payment_method" in payload or not partial:
        pm = payload.get("payment_method")
        if not isinstance(pm, str) or pm.strip() not in PAYMENT_METHODS:
            validation_errors["payment_method"] = f"payment_method must be one of: {', '.join(sorted(PAYMENT_METHODS))}"
        else:
            cleaned["payment_method"] = pm.strip()

    # payment_status
    if "payment_status" in payload or not partial:
        ps = payload.get("payment_status")
        if not isinstance(ps, str) or ps.strip() not in PAYMENT_STATUSES:
            validation_errors["payment_status"] = f"payment_status must be one of: {', '.join(sorted(PAYMENT_STATUSES))}"
        else:
            cleaned["payment_status"] = ps.strip()

    # transaction_id (optional)
    if "transaction_id" in payload:
        cleaned["transaction_id"] = payload.get("transaction_id")

    # payment_date
    if "payment_date" in payload or not partial:
        pd = _parse_date(payload.get("payment_date"))
        if pd is None:
            validation_errors["payment_date"] = "payment_date must be a valid ISO date (YYYY-MM-DD)"
        else:
            cleaned["payment_date"] = pd

    # notes
    if "notes" in payload:
        notes = payload.get("notes")
        cleaned["notes"] = notes.strip() if isinstance(notes, str) else notes

    if partial and not cleaned and not validation_errors:
        return True, {}, None

    if validation_errors:
        return False, None, validation_errors
    return True, cleaned, None


def _booking_fully_paid(booking_id: int) -> bool:
    # Prevent duplicate successful payments for the same booking by checking sums.
    total_paid = (
        db.session.query(db.func.coalesce(db.func.sum(Payment.amount), 0.0))
        .filter(Payment.booking_id == booking_id, Payment.payment_status == "Paid")
        .scalar()
    )
    booking = Booking.query.get(booking_id)
    if not booking:
        return False
    try:
        return float(total_paid or 0.0) >= float(booking.total_amount)
    except Exception:
        return False


def _update_booking_payment_status_if_needed(*, booking: Booking, old_status: str | None, new_status: str):
    # When payment_status becomes Paid/Refunded, update Booking.payment_status accordingly.
    if new_status == "Paid" and booking.payment_status != "Paid":
        booking.payment_status = "Paid"
    if new_status == "Refunded" and booking.payment_status != "Refunded":
        booking.payment_status = "Refunded"


def _hotel_name() -> str:
    # No access to frontend config; keep constant.
    return "Hotel Management"


@payments_bp.get("")
def get_payments():
    query = Payment.query

    payment_status = request.args.get("payment_status")
    payment_method = request.args.get("payment_method")
    customer_email = request.args.get("customer_email")
    booking_id = request.args.get("booking_id")

    if payment_status:
        query = query.filter(Payment.payment_status == payment_status.strip())
    if payment_method:
        query = query.filter(Payment.payment_method == payment_method.strip())
    if customer_email:
        query = query.filter(Payment.customer_email == customer_email.strip())
    if booking_id:
        try:
            bid = int(booking_id)
            query = query.filter(Payment.booking_id == bid)
        except ValueError:
            return _json_error("booking_id must be an integer", 400)

    sort = (request.args.get("sort") or "").strip()
    if sort == "payment_date":
        query = query.order_by(asc(Payment.payment_date))
    elif sort == "created_at":
        query = query.order_by(asc(Payment.created_at))
    elif sort == "amount":
        query = query.order_by(asc(Payment.amount))

    payments = query.all()
    return jsonify({"success": True, "data": [_payment_to_dict(p) for p in payments]})


@payments_bp.get("/<int:payment_id>")
def get_payment(payment_id: int):
    payment = Payment.query.get(payment_id)
    if not payment:
        return _json_error("Payment not found", 404)
    return jsonify({"success": True, "data": _payment_to_dict(payment)})


def create_payment():
    payload = request.get_json(silent=True) or {}

    ok, cleaned, validation_errors = _validate_payment_payload(payload, partial=False)
    if not ok or cleaned is None:
        return _json_error("Validation failed", 400, validation_errors=validation_errors)

    booking = Booking.query.get(cleaned["booking_id"])
    if not booking:
        return _json_error("Booking not found", 404)

    if _booking_fully_paid(booking.id):
        return _json_error("Booking already fully paid", 409)

    payment = Payment(
        payment_number=_generate_payment_number(),
        invoice_number=_generate_invoice_number(),
        booking_id=cleaned["booking_id"],
        customer_name=cleaned["customer_name"],
        customer_email=cleaned["customer_email"],
        amount=cleaned["amount"],
        payment_method=cleaned["payment_method"],
        payment_status=cleaned["payment_status"],
        transaction_id=cleaned.get("transaction_id"),
        payment_date=cleaned.get("payment_date"),
        notes=cleaned.get("notes"),
    )

    old_booking_status = booking.payment_status

    try:
        db.session.add(payment)
        # Business rules for booking update on status.
        _update_booking_payment_status_if_needed(
            booking=booking,
            old_status=old_booking_status,
            new_status=payment.payment_status,
        )
        db.session.add(booking)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _json_error("Payment conflict (unique constraint)", 409)
    except Exception:
        db.session.rollback()
        return _json_error("Failed to create payment", 500)

    return jsonify({"success": True, "data": _payment_to_dict(payment)}), 201


def update_payment(payment_id: int):
    payment = Payment.query.get(payment_id)
    if not payment:
        return _json_error("Payment not found", 404)

    payload = request.get_json(silent=True) or {}
    ok, cleaned, validation_errors = _validate_payment_payload(payload, partial=True)
    if not ok or cleaned is None:
        return _json_error("Validation failed", 400, validation_errors=validation_errors)

    if not cleaned:
        return _json_error("No valid fields provided to update", 400)

    booking = Booking.query.get(cleaned.get("booking_id", payment.booking_id))
    if not booking:
        return _json_error("Booking not found", 404)

    old_status = payment.payment_status

    for key, value in cleaned.items():
        setattr(payment, key, value)

    try:
        _update_booking_payment_status_if_needed(
            booking=booking, old_status=old_status, new_status=payment.payment_status
        )
        db.session.add(payment)
        db.session.add(booking)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _json_error("Update conflict (unique constraint)", 409)
    except Exception:
        db.session.rollback()
        return _json_error("Failed to update payment", 500)

    return jsonify({"success": True, "data": _payment_to_dict(payment)})


def delete_payment(payment_id: int):
    payment = Payment.query.get(payment_id)
    if not payment:
        return _json_error("Payment not found", 404)

    try:
        db.session.delete(payment)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _json_error("Failed to delete payment", 409)
    except Exception:
        db.session.rollback()
        return _json_error("Failed to delete payment", 500)

    return jsonify({"success": True, "message": "Payment deleted"})


@payments_bp.get("/<int:payment_id>/invoice")
def payment_invoice(payment_id: int):
    payment = Payment.query.get(payment_id)
    if not payment:
        return _json_error("Payment not found", 404)

    booking = Booking.query.get(payment.booking_id)
    if not booking:
        return _json_error("Booking not found for invoice", 404)

    # Try to fetch room number if available (no other file modifications).
    room_number: str | None = None
    try:
        from models.room import Room

        room = Room.query.get(booking.room_id)
        if room:
            room_number = room.room_number
    except Exception:
        room_number = None

    # Simple tax/grand total calculation (no DB tax field specified).
    tax = round(float(payment.amount) * 0.0, 2)
    grand_total = float(payment.amount) + float(tax)

    invoice = {
        "hotel_name": _hotel_name(),
        "invoice_number": payment.invoice_number,
        "payment_number": payment.payment_number,
        "booking_number": booking.booking_number,
        "customer_name": payment.customer_name,
        "customer_email": payment.customer_email,
        "room_number": room_number,
        "check_in_date": booking.check_in_date.isoformat() if booking.check_in_date else None,
        "check_out_date": booking.check_out_date.isoformat() if booking.check_out_date else None,
        "payment_method": payment.payment_method,
        "payment_status": payment.payment_status,
        "amount": payment.amount,
        "tax": tax,
        "grand_total": grand_total,
        "payment_date": payment.payment_date.isoformat() if payment.payment_date else None,
    }

    return jsonify({"success": True, "data": invoice})



