"""ORM models. Importing this package registers every model on ``Base.metadata``.

Alembic and ``create_all`` both rely on this side-effect, so import models from
here (``from app.models import Analysis``) rather than reaching into submodules.
"""

from app.db.base_class import Base
from app.models.analysis import Analysis
from app.models.candidate import Candidate, CandidateEvidence
from app.models.clue import VisualClue
from app.models.image import ImageMetadata, UploadedImage
from app.models.location import Location
from app.models.system import ApiUsage, AuditLog, SearchCache
from app.models.user import User

__all__ = [
    "Base",
    "User",
    "Analysis",
    "UploadedImage",
    "ImageMetadata",
    "VisualClue",
    "Location",
    "Candidate",
    "CandidateEvidence",
    "ApiUsage",
    "SearchCache",
    "AuditLog",
]
