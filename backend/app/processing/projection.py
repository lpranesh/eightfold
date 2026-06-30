"""Applies projection configuration to canonical output."""

from typing import Any
from app.models.canonical import CanonicalProfile
from app.models.requests import ProjectionConfigDTO


class Projector:
    """Creates a custom view of the canonical profile."""

    @classmethod
    def project(cls, profile: CanonicalProfile, config: ProjectionConfigDTO) -> dict[str, Any]:
        """Project the profile without modifying the original."""
        data = profile.model_dump(exclude_none=True)
        
        if config.include_fields:
            data = {k: v for k, v in data.items() if k in config.include_fields}
            
        if config.exclude_fields:
            data = {k: v for k, v in data.items() if k not in config.exclude_fields}
            
        if config.rename_fields:
            for old_key, new_key in config.rename_fields.items():
                if old_key in data:
                    data[new_key] = data.pop(old_key)
                    
        return data
