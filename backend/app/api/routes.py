"""API Routing."""

from typing import Optional
from fastapi import APIRouter, File, Form, UploadFile
from app.models.requests import ProjectionConfigDTO
from app.models.responses import TransformResponse
from app.pipeline.engine import TransformationService


router = APIRouter()
service = TransformationService()

@router.get("/health")
def health():
    import datetime
    from app.core.config import settings
    return {
        "status": "ok",
        "version": settings.VERSION,
        "timestamp": datetime.datetime.now().isoformat()
    }


@router.post("/transform", response_model=TransformResponse)
async def transform(
    files: list[UploadFile] = File(default=[]),
    github_url: Optional[str] = Form(None),
    linkedin_url: Optional[str] = Form(None),
    projection_json: Optional[str] = Form(None)
):
    """Transform uploaded documents and profile URLs into a canonical candidate profile."""
    # Process files
    file_contents = []
    for f in files:
        if f.filename:
            content = await f.read()
            file_contents.append((content, f.filename))
            
    # Process projection
    projection = None
    if projection_json:
        import json
        try:
            proj_dict = json.loads(projection_json)
            projection = ProjectionConfigDTO(**proj_dict)
        except Exception:
            pass
            
    return await service.transform(
        files=file_contents,
        github_url=github_url,
        linkedin_url=linkedin_url,
        projection=projection
    )
