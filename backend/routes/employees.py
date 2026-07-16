from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from database import db
from models.employee import Employee
from utils.validators import validate_email, validate_phone


employees_bp = Blueprint("employees", __name__, url_prefix="/api/employees")


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


def _employees_to_dict(e: Employee) -> dict[str, Any]:
    return {
        "id": e.id,
        "full_name": e.full_name,
        "email": e.email,
        "phone": getattr(e, "phone", None),
        "department": e.department,
        "designation": getattr(e, "designation", None),
        "role": getattr(e, "role", None),
        "salary": getattr(e, "salary", None),
        "status": e.status,
        "created_at": e.created_at.isoformat() if hasattr(e, "created_at") and e.created_at else None,
        "updated_at": e.updated_at.isoformat() if hasattr(e, "updated_at") and e.updated_at else None,
    }


def _validate_employee_payload(payload: dict[str, Any], *, partial: bool = False):
    cleaned: dict[str, Any] = {}
    validation_errors: dict[str, Any] = {}

    def _req(field: str):
        if field not in payload or payload.get(field) in (None, ""):
            validation_errors[field] = "This field is required"

    if not partial:
        for f in ["full_name", "email", "department", "designation", "salary", "status"]:
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

    # phone optional
    if "phone" in payload:
        pv = validate_phone(payload.get("phone"))
        if payload.get("phone") in (None, ""):
            cleaned["phone"] = None
        elif pv is None:
            validation_errors["phone"] = "phone is invalid"
        else:
            cleaned["phone"] = pv

    for f in ["department", "designation"]:
        if f in payload or not partial:
            v = payload.get(f)
            if not isinstance(v, str) or not v.strip():
                validation_errors[f] = f"{f} must be a non-empty string"
            else:
                cleaned[f] = v.strip()

    if "status" in payload or not partial:
        st = payload.get("status")
        if not isinstance(st, str) or not st.strip():
            validation_errors["status"] = "status must be a non-empty string"
        else:
            cleaned["status"] = st.strip()

    if "salary" in payload or not partial:
        try:
            sal = float(payload.get("salary"))
            if sal < 0:
                raise ValueError
            cleaned["salary"] = sal
        except Exception:
            validation_errors["salary"] = "salary must be a number >= 0"

    if partial and not cleaned and not validation_errors:
        return True, {}, {}

    if validation_errors:
        return False, None, validation_errors
    return True, cleaned, {}


@employees_bp.get("")
def list_employees():
    page, page_size = _parse_pagination()
    search = (request.args.get("search") or "").strip()

    sort = (request.args.get("sort") or "").strip()
    allowed = {"id", "full_name", "email", "department", "designation", "salary", "status"}
    desc = sort.startswith("-")
    col = sort[1:] if desc else sort
    if sort and col not in allowed:
        sort = ""

    query = Employee.query
    if search:
        like = f"%{search}%"
        query = query.filter(
            (Employee.full_name.ilike(like))
            | (Employee.email.ilike(like))
            | (Employee.department.ilike(like))
            | (func.cast(getattr(Employee, "designation"), db.String).ilike(like))
        )

    total = query.count()

    if sort:
        qcol = getattr(Employee, col, None)
        if qcol is not None:
            query = query.order_by(qcol.desc() if desc else qcol.asc())

    items = query.offset((page - 1) * page_size).limit(page_size).all()

    data = {
        "items": [_employees_to_dict(e) for e in items],
        "page": page,
        "page_size": page_size,
        "total": total,
    }
    return _json_ok("Employees fetched", data=data)


@employees_bp.get("/<int:employee_id>")
def get_employee(employee_id: int):
    e = Employee.query.get(employee_id)
    if not e:
        return _json_error("Employee not found", 404)
    return _json_ok("Employee fetched", data=_employees_to_dict(e))


@employees_bp.post("")
def create_employee():
    payload = request.get_json(silent=True) or {}
    ok, cleaned, validation_errors = _validate_employee_payload(payload, partial=False)
    if not ok or cleaned is None:
        return _json_error("Validation failed", 400, validation_errors=validation_errors)

    e = Employee(
        full_name=cleaned["full_name"],
        email=cleaned["email"],
        phone=cleaned.get("phone"),
        department=cleaned["department"],
        designation=cleaned["designation"],
        salary=cleaned["salary"],
        status=cleaned["status"],
        role=cleaned.get("role"),
    )

    try:
        db.session.add(e)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _json_error("Employee email must be unique", 400, validation_errors={"email": "unique"})

    return _json_ok("Employee created", data=_employees_to_dict(e), status_code=201)


@employees_bp.put("/<int:employee_id>")
def update_employee(employee_id: int):
    e = Employee.query.get(employee_id)
    if not e:
        return _json_error("Employee not found", 404)

    payload = request.get_json(silent=True) or {}
    ok, cleaned, validation_errors = _validate_employee_payload(payload, partial=True)
    if not ok or cleaned is None:
        return _json_error("Validation failed", 400, validation_errors=validation_errors)
    if not cleaned:
        return _json_error("No valid fields provided to update", 400)

    for k, v in cleaned.items():
        setattr(e, k, v)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _json_error("Employee email must be unique", 400, validation_errors={"email": "unique"})

    return _json_ok("Employee updated", data=_employees_to_dict(e))


@employees_bp.delete("/<int:employee_id>")
def delete_employee(employee_id: int):
    e = Employee.query.get(employee_id)
    if not e:
        return _json_error("Employee not found", 404)

    db.session.delete(e)
    db.session.commit()
    return _json_ok("Employee deleted", data=None)

