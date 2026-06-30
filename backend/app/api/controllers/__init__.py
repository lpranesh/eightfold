"""API controllers — request/response handling only.

No business logic here. All logic is delegated to services.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters import SourceAdapter
from app.config.settings import Settings, get_settings
from app.database import DatabaseManager
from app.exceptions import APIException, FileUploadException
from app.factories import create_default_parser_factory
from app.models.domain.enums import SourceType
from app.models.domain.projection import ProjectionConfig
from app.models.dto import (
    CandidateDetailResponse, CandidateListResponse, FieldExplanation,
    HealthResponse, MetadataResponse, ProjectionRequest, ProjectionResponse,
    TransformResponse,
)
from app.repositories import CandidateRepository
from app.services.candidate_service import CandidateService
from app.services.pipeline import TransformationPipeline

logger = logging.getLogger(__name__)

router = APIRouter()

# Module-level references set during app startup
_db_manager: Optional[DatabaseManager] = None
_settings: Optional[Settings] = None


def set_dependencies(db_manager: DatabaseManager, settings: Settings) -> None:
    """Set module dependencies during app startup."""
    global _db_manager, _settings
    _db_manager = db_manager
    _settings = settings


async def _get_service() -> CandidateService:
    """Build the service with all dependencies. Per-request lifecycle."""
    if _db_manager is None or _settings is None:
        raise APIException(message="Application not initialized")

    session_gen = _db_manager.get_session()
    session = await session_gen.__anext__()

    repository = CandidateRepository(session)
    parser_factory = create_default_parser_factory(ocr_enabled=_settings.ocr_enabled)
    pipeline = TransformationPipeline(
        parser_factory=parser_factory,
        source_priorities=_settings.source_priorities,
    )
    return CandidateService(repository=repository, pipeline=pipeline)


@router.post("/transform", response_model=TransformResponse)
async def transform_sources(
    files: list[UploadFile] = File(...),
    source_types: list[str] = Form(...),
) -> TransformResponse:
    """Upload multiple source files and transform into a canonical profile.

    Accepts multipart form data with files and corresponding source type strings.
    """
    if len(files) != len(source_types):
        raise FileUploadException(
            message="Number of files must match number of source_types",
            details={"files": len(files), "source_types": len(source_types)},
        )

    if not files:
        raise FileUploadException(message="At least one file is required")

    service = await _get_service()

    # Read files and resolve source types
    file_tuples: list[tuple[str, bytes, SourceType]] = []
    for upload_file, st_str in zip(files, source_types):
        try:
            source_type = SourceType(st_str)
        except ValueError:
            raise FileUploadException(
                message=f"Invalid source type: {st_str}",
                details={"valid_types": [s.value for s in SourceType]},
            )
        content = await upload_file.read()
        filename = upload_file.filename or "unknown"
        file_tuples.append((filename, content, source_type))

    return await service.transform_sources(file_tuples)


@router.get("/candidates", response_model=CandidateListResponse)
async def list_candidates(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> CandidateListResponse:
    """List all candidates with pagination."""
    service = await _get_service()
    return await service.list_candidates(limit=limit, offset=offset)


@router.get("/candidate/{candidate_id}", response_model=CandidateDetailResponse)
async def get_candidate(candidate_id: str) -> CandidateDetailResponse:
    """Get full candidate detail by ID."""
    service = await _get_service()
    return await service.get_candidate(candidate_id)


@router.get("/candidate/{candidate_id}/metadata", response_model=MetadataResponse)
async def get_candidate_metadata(candidate_id: str) -> MetadataResponse:
    """Get candidate transformation metadata."""
    service = await _get_service()
    return await service.get_candidate_metadata(candidate_id)


@router.post("/candidate/{candidate_id}/projection", response_model=ProjectionResponse)
async def get_projection(
    candidate_id: str,
    request: ProjectionRequest,
) -> ProjectionResponse:
    """Apply a projection to a candidate profile."""
    config = ProjectionConfig(
        include_fields=request.include_fields,
        exclude_fields=request.exclude_fields,
        rename_fields=request.rename_fields,
        hide_metadata=request.hide_metadata,
    )
    service = await _get_service()
    return await service.get_projection(candidate_id, config)


@router.get("/candidate/{candidate_id}/explain/{field_name}", response_model=FieldExplanation)
async def explain_field(candidate_id: str, field_name: str) -> FieldExplanation:
    """Get a detailed explanation of how a field value was determined."""
    service = await _get_service()
    return await service.explain_field(candidate_id, field_name)


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    db_status = "unknown"
    if _db_manager:
        healthy = await _db_manager.check_health()
        db_status = "healthy" if healthy else "unhealthy"
    return HealthResponse(
        status="ok",
        version=_settings.app_version if _settings else "unknown",
        database=db_status,
        timestamp=datetime.utcnow(),
    )
