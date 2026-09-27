"""Alembic metadata target.

Importing this module pulls in ``Base`` with every model registered, so
``target_metadata = Base.metadata`` sees the full schema.
"""

from app.db.base_class import Base  # noqa: F401
from app.models import *  # noqa: F401,F403
