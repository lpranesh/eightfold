"""SQLAlchemy ORM models for PostgreSQL persistence.

These map directly to database tables. Domain ↔ Database conversion
happens in the repository layer.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class CandidateModel(Base):
    """Persistent candidate record.
    
    A simplified table storing the unified canonical profile and its metadata
    as JSONB for easy explainability and fast retrieval without complex joins.
    """

    __tablename__ = "candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canonical_profile = Column(JSONB, nullable=False)
    metadata_record = Column(JSONB, nullable=False)
    provenance_record = Column(JSONB, nullable=False, default=dict)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
