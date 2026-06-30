"""Initial migration — create all tables.

Revision ID: 001
Create Date: 2026-07-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("full_name", sa.String(255), nullable=True, index=True),
        sa.Column("first_name", sa.String(127), nullable=True),
        sa.Column("last_name", sa.String(127), nullable=True),
        sa.Column("email", sa.String(255), nullable=True, index=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("current_title", sa.String(255), nullable=True),
        sa.Column("current_company", sa.String(255), nullable=True),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("years_of_experience", sa.Float, nullable=True),
        sa.Column("skills", sa.JSON, nullable=True),
        sa.Column("experience", sa.JSON, nullable=True),
        sa.Column("education", sa.JSON, nullable=True),
        sa.Column("certifications", sa.JSON, nullable=True),
        sa.Column("languages", sa.JSON, nullable=True),
        sa.Column("github_url", sa.String(512), nullable=True),
        sa.Column("linkedin_url", sa.String(512), nullable=True),
        sa.Column("portfolio_url", sa.String(512), nullable=True),
        sa.Column("overall_confidence", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("overall_confidence_level", sa.String(20), nullable=False, server_default="low"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "candidate_metadata",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("transformation_run_id", sa.String(36), nullable=False),
        sa.Column("sources_processed", sa.JSON, nullable=False),
        sa.Column("total_fields_extracted", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_conflicts_resolved", sa.Integer, nullable=False, server_default="0"),
        sa.Column("overall_confidence", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("processing_duration_ms", sa.Float, nullable=True),
        sa.Column("warnings", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "source_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_size_bytes", sa.Integer, nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("parse_warnings", sa.JSON, nullable=True),
        sa.Column("processed_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "source_values",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("field_name", sa.String(100), nullable=False, index=True),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("raw_value", sa.JSON, nullable=True),
        sa.Column("normalized_value", sa.JSON, nullable=True),
        sa.Column("is_selected", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("selection_reason", sa.Text, nullable=True),
        sa.Column("normalizations_applied", sa.JSON, nullable=True),
        sa.Column("extraction_method", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "transformation_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("stages", sa.JSON, nullable=True),
        sa.Column("total_duration_ms", sa.Float, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("started_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )

    op.create_table(
        "projection_configurations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("include_fields", sa.JSON, nullable=True),
        sa.Column("exclude_fields", sa.JSON, nullable=True),
        sa.Column("rename_fields", sa.JSON, nullable=True),
        sa.Column("hide_metadata", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("projection_configurations")
    op.drop_table("transformation_runs")
    op.drop_table("source_values")
    op.drop_table("source_documents")
    op.drop_table("candidate_metadata")
    op.drop_table("candidates")
