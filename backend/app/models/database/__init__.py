"""SQLAlchemy ORM models for PostgreSQL persistence.

These map directly to database tables. Domain ↔ Database conversion
happens in the repository layer.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class CandidateModel(Base):
    """Persistent candidate record."""

    __tablename__ = "candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(255), nullable=True, index=True)
    first_name = Column(String(127), nullable=True)
    last_name = Column(String(127), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    current_title = Column(String(255), nullable=True)
    current_company = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    years_of_experience = Column(Float, nullable=True)
    skills = Column(JSON, nullable=True, default=list)
    experience = Column(JSON, nullable=True, default=list)
    education = Column(JSON, nullable=True, default=list)
    certifications = Column(JSON, nullable=True, default=list)
    languages = Column(JSON, nullable=True, default=list)
    github_url = Column(String(512), nullable=True)
    linkedin_url = Column(String(512), nullable=True)
    portfolio_url = Column(String(512), nullable=True)

    overall_confidence = Column(Float, nullable=False, default=0.0)
    overall_confidence_level = Column(String(20), nullable=False, default="low")

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    metadata_record = relationship(
        "CandidateMetadataModel",
        back_populates="candidate",
        uselist=False,
        cascade="all, delete-orphan",
    )
    source_documents = relationship(
        "SourceDocumentModel",
        back_populates="candidate",
        cascade="all, delete-orphan",
    )
    source_values = relationship(
        "SourceValueModel",
        back_populates="candidate",
        cascade="all, delete-orphan",
    )
    transformation_runs = relationship(
        "TransformationRunModel",
        back_populates="candidate",
        cascade="all, delete-orphan",
    )


class CandidateMetadataModel(Base):
    """Metadata about how the candidate profile was constructed."""

    __tablename__ = "candidate_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(
        UUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    transformation_run_id = Column(String(36), nullable=False)
    sources_processed = Column(JSON, nullable=False, default=list)
    total_fields_extracted = Column(Integer, nullable=False, default=0)
    total_conflicts_resolved = Column(Integer, nullable=False, default=0)
    overall_confidence = Column(Float, nullable=False, default=0.0)
    processing_duration_ms = Column(Float, nullable=True)
    warnings = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    candidate = relationship("CandidateModel", back_populates="metadata_record")


class SourceDocumentModel(Base):
    """Record of a source document that was processed."""

    __tablename__ = "source_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(
        UUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_type = Column(String(50), nullable=False)
    filename = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    content_hash = Column(String(64), nullable=True)
    parse_warnings = Column(JSON, nullable=True, default=list)
    processed_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    candidate = relationship("CandidateModel", back_populates="source_documents")


class SourceValueModel(Base):
    """Individual field values with provenance.

    Stores every value from every source for every field, enabling
    full provenance tracking and field-level explanation.
    """

    __tablename__ = "source_values"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(
        UUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
    )
    field_name = Column(String(100), nullable=False, index=True)
    source_type = Column(String(50), nullable=False)
    raw_value = Column(JSON, nullable=True)
    normalized_value = Column(JSON, nullable=True)
    is_selected = Column(Boolean, nullable=False, default=False)
    confidence = Column(Float, nullable=False, default=0.0)
    selection_reason = Column(Text, nullable=True)
    normalizations_applied = Column(JSON, nullable=True, default=list)
    extraction_method = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    candidate = relationship("CandidateModel", back_populates="source_values")


class TransformationRunModel(Base):
    """Record of a transformation pipeline execution."""

    __tablename__ = "transformation_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(
        UUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
    )
    status = Column(String(20), nullable=False, default="pending")
    stages = Column(JSON, nullable=True, default=list)
    total_duration_ms = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    candidate = relationship("CandidateModel", back_populates="transformation_runs")


class ProjectionConfigModel(Base):
    """Saved projection configurations."""

    __tablename__ = "projection_configurations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    include_fields = Column(JSON, nullable=True)
    exclude_fields = Column(JSON, nullable=True)
    rename_fields = Column(JSON, nullable=True, default=dict)
    hide_metadata = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
