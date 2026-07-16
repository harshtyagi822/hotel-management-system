from __future__ import annotations

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


def create_limiter(app):
    # defaults overridden per-route in decorators
    limiter = Limiter(
        app,
        key_func=get_remote_address,
        default_limits=[],
    )
    return limiter

