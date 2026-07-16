"""Authentication routes."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity
)


from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from middleware.auth import admin_required
from models.user import User
from utils.validators import validate_email, validate_phone, validate_password


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")



def _json(success: bool, message: str, status_code: int = 200, extra: dict[str, Any] | None = None):
    payload: dict[str, Any] = {"success": success, "message": message}
    if extra:
        payload.update(extra)
    resp = jsonify(payload)
    resp.status_code = status_code
    return resp


def _require_json_fields(required: list[str]) -> dict[str, Any] | None:
    data = request.get_json(silent=True) or {}
    # Treat only missing/empty strings as missing.
    missing = [f for f in required if data.get(f) is None or (isinstance(data.get(f), str) and not data.get(f).strip()) or data.get(f) == ""]

    if missing:
        return _json(False, f"Missing required fields: {', '.join(missing)}", 400)
    return data


@auth_bp.post("/register")
def register() -> Any:
    data_or_resp = _require_json_fields(["full_name", "email", "phone", "password"])
    if not isinstance(data_or_resp, dict):
        return data_or_resp

    data = data_or_resp
    full_name = (data.get("full_name") or "").strip()
    email = validate_email(data.get("email"))
    phone = validate_phone(data.get("phone"))
    password = data.get("password")

    if not full_name:
        return _json(False, "full_name is required", 400)
    if not email:
        return _json(False, "Invalid email", 400)
    if not phone:
        return _json(False, "Invalid phone", 400)
    if not validate_password(password):
        return _json(False, "Password must be at least 8 characters", 400)

    existing_email = db.session.execute(db.select(User).where(User.email == email)).scalar_one_or_none()
    if existing_email:
        return _json(False, "Email already exists", 400)

    existing_phone = db.session.execute(db.select(User).where(User.phone == phone)).scalar_one_or_none()
    if existing_phone:
        return _json(False, "Phone already exists", 400)

    password_hash = generate_password_hash(password)

    user = User(
        full_name=full_name,
        email=email,
        phone=phone,
        password_hash=password_hash,
        role="Customer",
        is_active=True,
    )
    db.session.add(user)
    db.session.commit()

    return _json(True, "Registration Successful", 200)


@auth_bp.post("/login")
def login() -> Any:
    data_or_resp = _require_json_fields(["email", "password"])
    if not isinstance(data_or_resp, dict):
        return data_or_resp
    data = data_or_resp

    email = validate_email(data.get("email"))
    password = data.get("password")

    if not email:
        return _json(False, "Invalid email", 400)
    if not password:
        return _json(False, "Password is required", 400)

    user = db.session.execute(db.select(User).where(User.email == email)).scalar_one_or_none()
    if not user or not check_password_hash(user.password_hash, password):
        return _json(False, "Invalid credentials", 401)

    if not user.is_active:
        return _json(False, "Account is inactive", 403)

    access_token = create_access_token(
        identity=user.to_token_claims(),
        additional_claims=user.to_token_claims(),
    )

    refresh_token = create_refresh_token(
        identity=user.to_token_claims(),
        additional_claims=user.to_token_claims(),
    )

    return _json(
        True,
        "Login Successful",
        200,
        extra={
            "token": access_token,
            "refresh_token": refresh_token,
            "user": user.to_public_dict(),
        },
    )




@auth_bp.get("/profile")
@jwt_required()
def profile() -> Any:
    identity = get_jwt_identity() or {}
    user_id = identity.get("id") if isinstance(identity, dict) else None
    if not user_id:
        return _json(False, "Invalid token", 401)

    user = db.session.get(User, int(user_id))
    if not user:
        return _json(False, "User not found", 404)

    return _json(True, "Profile retrieved", 200, extra={"user": user.to_public_dict()})


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh() -> Any:
    # Issue a new access token using refresh token identity/claims.
    identity = get_jwt_identity() or {}
    user_id = identity.get("id") if isinstance(identity, dict) else None
    if not user_id:
        return _json(False, "Invalid refresh token", 401)

    user = db.session.get(User, int(user_id))
    if not user or not user.is_active:
        return _json(False, "User not found", 404)

    access_token = create_access_token(
        identity=user.to_token_claims(),
        additional_claims=user.to_token_claims(),
    )

    return _json(True, "Token refreshed", 200, extra={"token": access_token})


@auth_bp.post("/change-password")
@jwt_required()
def change_password() -> Any:

    data_or_resp = _require_json_fields(["old_password", "new_password"])
    if not isinstance(data_or_resp, dict):
        return data_or_resp
    data = data_or_resp

    identity = get_jwt_identity() or {}
    user_id = identity.get("id") if isinstance(identity, dict) else None
    if not user_id:
        return _json(False, "Invalid token", 401)

    user = db.session.get(User, int(user_id))
    if not user:
        return _json(False, "User not found", 404)

    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if not old_password or not check_password_hash(user.password_hash, old_password):
        return _json(False, "Old password is incorrect", 400)

    if not validate_password(new_password):
        return _json(False, "Password must be at least 8 characters", 400)

    user.password_hash = generate_password_hash(new_password)
    db.session.commit()

    return _json(True, "Password updated", 200)


@auth_bp.post("/create-staff")
@jwt_required()
@admin_required
def create_staff() -> Any:
    data_or_resp = _require_json_fields(["full_name", "email", "phone", "password", "role"])
    if not isinstance(data_or_resp, dict):
        return data_or_resp
    data = data_or_resp

    role = (data.get("role") or "").strip()
    if role not in User.roles():
        return _json(False, "Invalid role", 400)
    if role != "Receptionist":
        return _json(False, "Only Receptionist staff can be created", 403)

    full_name = (data.get("full_name") or "").strip()
    email = validate_email(data.get("email"))
    phone = validate_phone(data.get("phone"))
    password = data.get("password")

    if not full_name:
        return _json(False, "full_name is required", 400)
    if not email:
        return _json(False, "Invalid email", 400)
    if not phone:
        return _json(False, "Invalid phone", 400)
    if not validate_password(password):
        return _json(False, "Password must be at least 8 characters", 400)

    existing_email = db.session.execute(db.select(User).where(User.email == email)).scalar_one_or_none()
    if existing_email:
        return _json(False, "Email already exists", 400)

    existing_phone = db.session.execute(db.select(User).where(User.phone == phone)).scalar_one_or_none()
    if existing_phone:
        return _json(False, "Phone already exists", 400)

    user = User(
        full_name=full_name,
        email=email,
        phone=phone,
        password_hash=generate_password_hash(password),
        role=role,
        is_active=True,
    )
    db.session.add(user)
    db.session.commit()

    return _json(True, "Staff created", 200)

