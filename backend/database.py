"""Database initialization and SQLAlchemy helpers."""

from __future__ import annotations

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Engine

from config import Config



db = SQLAlchemy()


def _mysql_uri(cfg: Config) -> str:
    # Use PyMySQL driver.
    return (
        f"mysql+pymysql://{cfg.MYSQL_USER}:{cfg.MYSQL_PASSWORD}"
        f"@{cfg.MYSQL_HOST}:{cfg.MYSQL_PORT}/{cfg.MYSQL_DATABASE}?charset=utf8mb4"
    )



def init_db(app, cfg: Config) -> None:
    """Initialize SQLAlchemy with the app."""

    app.config.setdefault("SQLALCHEMY_DATABASE_URI", _mysql_uri(cfg))
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    app.config.setdefault("SQLALCHEMY_ENGINE_OPTIONS", {
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    })

    db.init_app(app)


def get_engine() -> Engine:
    """Expose underlying SQLAlchemy engine (useful for migrations/health)."""

    return db.engine

