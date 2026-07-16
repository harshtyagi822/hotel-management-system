from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request
from sqlalchemy import asc
from sqlalchemy.exc import IntegrityError

from database import db
from models.room import Room


rooms_bp = Blueprint("rooms", __name__, url_prefix="/api/rooms")

ROOM_STATUSES = {"Available", "Booked", "Maintenance"}


def _json_error(message: str, status_code: int = 400):
    resp = jsonify({"success": False, "message": message})
    resp.status_code = status_code
    return resp


def _validate_room_payload(payload: dict[str, Any], *, partial: bool = False):
    """Validate room creation/update payload.

    Returns (ok, cleaned_or_none, error_or_none)
    """
    cleaned: dict[str, Any] = {}

    if not partial:
        required_fields = ["room_number", "room_type", "price_per_night", "capacity", "status"]
        missing = [
            f
            for f in required_fields
            if f not in payload or payload.get(f) in (None, "")
        ]
        if missing:
            return False, None, f"Missing required fields: {', '.join(missing)}"

    if "room_number" in payload:
        room_number = (payload.get("room_number") or "").strip() if payload.get("room_number") is not None else None
        if not room_number:
            return False, None, "room_number is required"
        cleaned["room_number"] = room_number

    if "room_type" in payload:
        room_type = (payload.get("room_type") or "").strip() if payload.get("room_type") is not None else None
        if not room_type:
            return False, None, "room_type is required"
        cleaned["room_type"] = room_type

    if "price_per_night" in payload:
        try:
            price_f = float(payload.get("price_per_night"))
        except (TypeError, ValueError):
            return False, None, "price_per_night must be a number"
        if price_f <= 0:
            return False, None, "price_per_night must be > 0"
        cleaned["price_per_night"] = price_f

    if "capacity" in payload:
        try:
            cap_i = int(payload.get("capacity"))
        except (TypeError, ValueError):
            return False, None, "capacity must be an integer"
        if cap_i <= 0:
            return False, None, "capacity must be > 0"
        cleaned["capacity"] = cap_i

    if "status" in payload:
        status = (payload.get("status") or "").strip()
        if status not in ROOM_STATUSES:
            return False, None, f"status must be one of: {', '.join(sorted(ROOM_STATUSES))}"
        cleaned["status"] = status

    elif not partial:
        # required by POST
        return False, None, "status is required"

    if "description" in payload:
        desc = payload.get("description")
        cleaned["description"] = desc.strip() if isinstance(desc, str) else desc

    if "image_url" in payload:
        img = payload.get("image_url")
        cleaned["image_url"] = img.strip() if isinstance(img, str) else img

    if not cleaned and partial:
        return True, {}, None

    return True, cleaned, None


def _room_to_dict(room: Room) -> dict[str, Any]:
    return {
        "id": room.id,
        "room_number": room.room_number,
        "room_type": room.room_type,
        "price_per_night": room.price_per_night,
        "capacity": room.capacity,
        "status": room.status,
        "description": room.description,
        "image_url": room.image_url,
        "created_at": room.created_at.isoformat() if room.created_at else None,
        "updated_at": room.updated_at.isoformat() if room.updated_at else None,
    }


@rooms_bp.get("")
def get_rooms():
    query = Room.query

    status = request.args.get("status")
    rtype = request.args.get("type")
    capacity = request.args.get("capacity")

    if status:
        query = query.filter(Room.status == status.strip())

    if rtype:
        query = query.filter(Room.room_type == rtype.strip())

    if capacity not in (None, ""):
        try:
            cap_i = int(capacity)
        except ValueError:
            return _json_error("capacity must be an integer", 400)
        query = query.filter(Room.capacity == cap_i)

    sort = (request.args.get("sort") or "").strip()
    if sort == "price":
        query = query.order_by(asc(Room.price_per_night))
    elif sort == "room_number":
        query = query.order_by(asc(Room.room_number))

    rooms = query.all()
    return jsonify({"success": True, "data": [_room_to_dict(r) for r in rooms]})


@rooms_bp.get("/<int:room_id>")
def get_room(room_id: int):
    room = Room.query.get(room_id)
    if not room:
        return _json_error("Room not found", 404)
    return jsonify({"success": True, "data": _room_to_dict(room)})


@rooms_bp.post("")
def create_room():
    payload = request.get_json(silent=True) or {}

    ok, cleaned, err = _validate_room_payload(payload, partial=False)
    if not ok or cleaned is None:
        return _json_error(err or "Invalid payload", 400)

    room = Room(
        room_number=cleaned["room_number"],
        room_type=cleaned["room_type"],
        price_per_night=cleaned["price_per_night"],
        capacity=cleaned["capacity"],
        status=cleaned["status"],
        description=cleaned.get("description"),
        image_url=cleaned.get("image_url"),
    )

    try:
        db.session.add(room)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _json_error("room_number must be unique", 400)

    return jsonify({"success": True, "data": _room_to_dict(room)}), 201


@rooms_bp.put("/<int:room_id>")
def update_room(room_id: int):
    room = Room.query.get(room_id)
    if not room:
        return _json_error("Room not found", 404)

    payload = request.get_json(silent=True) or {}

    ok, cleaned, err = _validate_room_payload(payload, partial=True)
    if not ok or cleaned is None:
        return _json_error(err or "Invalid payload", 400)

    if not cleaned:
        return _json_error("No valid fields provided to update", 400)

    for key, value in cleaned.items():
        setattr(room, key, value)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _json_error("room_number must be unique", 400)

    return jsonify({"success": True, "data": _room_to_dict(room)})


@rooms_bp.delete("/<int:room_id>")
def delete_room(room_id: int):
    room = Room.query.get(room_id)
    if not room:
        return _json_error("Room not found", 404)

    db.session.delete(room)
    db.session.commit()
    return jsonify({"success": True, "message": "Room deleted"})


