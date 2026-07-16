"""SQLAlchemy models package."""

from __future__ import annotations

# Import models so Alembic/Flask can discover them.
# Keep imports local to avoid circular dependencies.

from models.user import User  # noqa: F401
from models.room import Room  # noqa: F401
from models.booking import Booking  # noqa: F401
from models.payment import Payment  # noqa: F401
from models.customer import Customer  # noqa: F401
from models.employee import Employee  # noqa: F401



