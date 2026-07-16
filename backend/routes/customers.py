from __future__ import annotations

from typing import Any, Optional

from flask import Blueprint, jsonify, request
from sqlalchemy import asc, func
from sqlalchemy.exc import IntegrityError

from database import db
from models.customer import Customer
from utils.validators import validate_email, validate_phone


customers_bp = Blueprint("customers", __name__, url_prefix="/api/customers")


def _json_ok(message: str = "OK", *, data: Any = None, status_code: int = 200):
    payload: dict[str, Any] = {"success": True, "message": message}
    if data is not None:
        payload["data"] = data
    resp = jsonify(payload)
    resp.status_code = status_code
    return resp


def _json_error(message: str, status_code: int = 400, *, validation_errors: dict[str, Any] | None = None):
    payload: dict[str, Any] = {"success": False, "message": message}
    if validation_errors is not None:
        payload["validation_errors"] = validation_errors
    resp = jsonify(payload)
    resp.status_code = status_code
    return resp


def _parse_pagination() -> tuple[int, int]:
    try:
        page = int(request.args.get("page", 1))
    except Exception:
        page = 1
    try:
        page_size = int(request.args.get("page_size", 10))
    except Exception:
        page_size = 10

    page = max(1, page)
    page_size = max(1, min(100, page_size))
    return page, page_size


def _sanitize_sort(sort: str | None, allowed: set[str]) -> str | None:
    if not sort:
        return None
    sort = sort.strip()
    if sort.startswith("-"):
        col = sort[1:]
        if col in allowed:
            return f"-{col}"
        return None
    if sort in allowed:
        return sort
    return None


def _customer_to_dict(c: Customer) -> dict[str, Any]:
    return {
        "id": c.id,
        "full_name": c.full_name,
        "email": c.email,
        "phone": c.phone,
        "created_at": c.created_at.isoformat() if hasattr(c, "created_at") and c.created_at else None,
        "updated_at": c.updated_at.isoformat() if hasattr(c, "updated_at") and c.updated_at else None,
    }


def _validate_customer_payload(payload: dict[str, Any], *, partial: bool = False) -> tuple[bool, dict[str, Any] | None, dict[str, Any]]:
    cleaned: dict[str, Any] = {}
    validation_errors: dict[str, Any] = {}

    def _req(field: str):
        if field not in payload or payload.get(field) in (None, ""):
            validation_errors[field] = "This field is required"

    if not partial:
        for f in ["full_name", "email", "phone"]:
            _req(f)

    if "full_name" in payload or not partial:
        v = payload.get("full_name")
        if not isinstance(v, str) or not v.strip():
            validation_errors["full_name"] = "full_name must be a non-empty string"
        else:
            cleaned["full_name"] = v.strip()

    if "email" in payload or not partial:
        ve = validate_email(payload.get("email"))
        if ve is None:
            validation_errors["email"] = "email is invalid"
        else:
            cleaned["email"] = ve

    if "phone" in payload or not partial:
        # phone may be null/empty
        vp = validate_phone(payload.get("phone"))
        if payload.get("phone") in (None, ""):
            if not partial:
                cleaned["phone"] = None
            else:
                # if partial and phone explicitly null, ignore
                if payload.get("phone") is None:
                    cleaned["phone"] = None
        elif vp is None:
            validation_errors["phone"] = "phone is invalid"
        else:
            cleaned["phone"] = vp

    if partial and not cleaned and not validation_errors:
        return True, {}, {}

    if validation_errors:
        return False, None, validation_errors
    return True, cleaned, {}


@customers_bp.get("")
def list_customers():
    page, page_size = _parse_pagination()
    search = (request.args.get("search") or "").strip()

    sort_raw = request.args.get("sort")
    allowed = {"id", "full_name", "email", "phone", "created_at", "updated_at"}
    sort = _sanitize_sort(sort_raw, allowed)

    query = Customer.query

    if search:
        like = f"%{search}%"
        query = query.filter(
            (Customer.full_name.ilike(like)) | (Customer.email.ilike(like)) | (func.cast(Customer.phone, db.String).ilike(like))
        )

    total = query.count()

    if sort:
        desc = sort.startswith("-")
        col = sort[1:] if desc else sort
        qcol = getattr(Customer, col, None)
        if qcol is not None:
            query = query.order_by(qcol.desc() if desc else qcol.asc())

    items = query.offset((page - 1) * page_size).limit(page_size).all()

    data = {
        "items": [_customer_to_dict(c) for c in items],
        "page": page,
        "page_size": page_size,
        "total": total,
    }
    return _json_ok("Customers fetched", data=data)


@customers_bp.get("/<int:customer_id>")
def get_customer(customer_id: int):
    c = Customer.query.get(customer_id)
    if not c:
        return _json_error("Customer not found", 404)
    return _json_ok("Customer fetched", data=_customer_to_dict(c))


@customers_bp.post("")
def create_customer():
    payload = request.get_json(silent=True) or {}
    ok, cleaned, validation_errors = _validate_customer_payload(payload, partial=False)
    if not ok or cleaned is None:
        return _json_error("Validation failed", 400, validation_errors=validation_errors)

    c = Customer(
        full_name=cleaned["full_name"],
        email=cleaned["email"],
        phone=cleaned.get("phone"),
    )

    try:
        db.session.add(c)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # Unique constraint
        return _json_error("Customer email/phone must be unique", 400, validation_errors={"email": "unique"})

    return _json_ok("Customer created", data=_customer_to_dict(c), status_code=201)


@customers_bp.put("/<int:customer_id>")
def update_customer(customer_id: int):
    c = Customer.query.get(customer_id)
    if not c:
        return _json_error("Customer not found", 404)

    payload = request.get_json(silent=True) or {}
    ok, cleaned, validation_errors = _validate_customer_payload(payload, partial=True)
    if not ok or cleaned is None:
        return _json_error("Validation failed", 400, validation_errors=validation_errors)
    if not cleaned:
        return _json_error("No valid fields provided to update", 400)

    for k, v in cleaned.items():
        setattr(c, k, v)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _json_error("Customer email/phone must be unique", 400, validation_errors={"email": "unique"})

    return _json_ok("Customer updated", data=_customer_to_dict(c))


@customers_bp.delete("/<int:customer_id>")
def delete_customer(customer_id: int):
    c = Customer.query.get(customer_id)
    if not c:
        return _json_error("Customer not found", 404)

    db.session.delete(c)
    db.session.commit()
    return _json_ok("Customer deleted", data=None)

