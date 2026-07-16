from __future__ import annotations

import os
import logging
from typing import Any

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from werkzeug.exceptions import HTTPException

from config import Config
from database import init_db, db
from routes.auth import auth_bp
from routes.rooms import rooms_bp
from routes.bookings import bookings_bp
from routes.dashboard import dashboard_bp
from routes.payments import payments_bp
from routes.contact import contact_bp
from logging_config import setup_logging
from flask_limiter_config import create_limiter





def create_app() -> Flask:
    app = Flask(__name__)

    # Load environment variables from .env (if present)
    # python-dotenv will populate os.environ so Config can read them.
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:
        pass


    # Fail-fast config
    cfg = Config()
    app.config.from_object(cfg)


    # CORS - restrict to FRONTEND_URL only
    cors = CORS(
        app,
        resources={r"/api/*": {"origins": [cfg.FRONTEND_URL]}},
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
        supports_credentials=False,
    )
    _ = cors

    # Initialize logging early
    setup_logging(app)
    logging.getLogger(__name__).info("Application startup")

    # Initialize extensions
    init_db(app, cfg)


    migrate = Migrate(app, db)
    _ = migrate

    jwt = JWTManager(app)
    _ = jwt

    # Rate limiting
    try:
        limiter = create_limiter(app)
        _ = limiter
    except Exception:
        # Do not break startup if limiter dependency/misconfig is missing.
        pass


    # Blueprints
    # NOTE: blueprints with empty/old auth routes might already be registered during dev.
    # We register the updated auth blueprint for Phase 2.
    app.register_blueprint(auth_bp)

    app.register_blueprint(rooms_bp)
    app.register_blueprint(bookings_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(contact_bp)

    # Security headers (reasonable defaults)
    @app.after_request
    def set_security_headers(response):
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        # Reasonable baseline CSP: allow self; frontend may load inline scripts/styles.
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
        )
        return response

    # Health endpoint
    @app.get("/api/health")

    def health() -> Any:
        return {"success": True, "message": "Hotel Management Backend Running"}

    register_error_handlers(app)

    # Debug mode comes from config
    app.debug = bool(app.config.get("DEBUG", False))

    return app


def register_error_handlers(app: Flask) -> None:
    """Centralized JSON error responses."""

    def _json_response(status_code: int, message: str):
        resp = jsonify({"success": False, "message": message})
        resp.status_code = status_code
        return resp

    @app.errorhandler(400)
    def bad_request(e: HTTPException):
        return _json_response(400, str(getattr(e, "description", "Bad Request")) or "Bad Request")

    @app.errorhandler(401)
    def unauthorized(e: HTTPException):
        return _json_response(401, str(getattr(e, "description", "Unauthorized")) or "Unauthorized")

    @app.errorhandler(403)
    def forbidden(e: HTTPException):
        return _json_response(403, str(getattr(e, "description", "Forbidden")) or "Forbidden")

    @app.errorhandler(404)
    def not_found(e: HTTPException):
        return _json_response(404, str(getattr(e, "description", "Not Found")) or "Not Found")

    @app.errorhandler(500)
    def internal_error(e: HTTPException):
        return _json_response(500, "Internal Server Error")

    # Catch any werkzeug HTTPException not covered above
    @app.errorhandler(HTTPException)
    def handle_http_exception(e: HTTPException):
        return _json_response(int(getattr(e, "code", 500) or 500), str(getattr(e, "description", "Error")) or "Error")

    # Generic fallback
    @app.errorhandler(Exception)
    def handle_exception(e: Exception):
        return _json_response(500, "Internal Server Error")


if __name__ == "__main__":
    application = create_app()
    application.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))

