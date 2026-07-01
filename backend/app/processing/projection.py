"""Applies projection configuration to canonical output."""

from typing import Any
from app.models.canonical import CanonicalProfile, CanonicalField
from app.models.requests import ProjectionConfigDTO


class Projector:
    """Creates a custom view of the canonical profile."""

    @classmethod
    def project(cls, profile: CanonicalProfile, config: ProjectionConfigDTO) -> dict[str, Any]:
        """Project the profile without modifying the original."""
        
        # Unwrap CanonicalFields to their raw values for the final output
        data = {}
        for k, v in profile.model_dump(exclude_none=True).items():
            if isinstance(v, list) and v and isinstance(v[0], dict) and "value" in v[0]:
                data[k] = [item["value"] for item in v]
            elif isinstance(v, dict) and "value" in v:
                data[k] = v["value"]
            else:
                data[k] = v
        
        if config.include_fields:
            data = {k: v for k, v in data.items() if k in config.include_fields}
            
        if config.exclude_fields:
            data = {k: v for k, v in data.items() if k not in config.exclude_fields}
            
        if config.rename_fields:
            for old_key, new_key in config.rename_fields.items():
                if old_key in data:
                    data[new_key] = data.pop(old_key)
                    
        return data
