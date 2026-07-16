"""JWT-based authorization decorators."""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar

from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request

F = TypeVar("F", bound=Callable[..., Any])


def _deny(message: str, status_code: int):
    resp = jsonify({"success": False, "message": message})
    resp.status_code = status_code
    return resp


def admin_required(fn: F) -> F:
    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any):
        verify_jwt_in_request()
        claims = get_jwt() or {}
        role = claims.get("role")
        if role != "Admin":
            return _deny("Admin access required", 403)
        return fn(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


def customer_required(fn: F) -> F:
    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any):
        verify_jwt_in_request()
        claims = get_jwt() or {}
        role = claims.get("role")
        if role != "Customer":
            return _deny("Customer access required", 403)
        return fn(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


def receptionist_required(fn: F) -> F:
    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any):
        verify_jwt_in_request()
        claims = get_jwt() or {}
        role = claims.get("role")
        if role != "Receptionist":
            return _deny("Receptionist access required", 403)
        return fn(*args, **kwargs)

    return wrapper  # type: ignore[return-value]

