from __future__ import annotations

from flask import Blueprint, jsonify

contact_bp = Blueprint("contact", __name__, url_prefix="/api/contact")


@contact_bp.get("/ping")
def contact_ping():
    # Stub endpoint for wiring; replace with real contact form endpoint in later phases.
    return jsonify({"success": True, "message": "Contact subsystem ready"})

