"""Projection engine — creates customized views of canonical profiles."""

import logging
from typing import Any

from app.exceptions import ProjectionException
from app.interfaces import ProjectionPolicyInterface
from app.models.domain.candidate import CanonicalProfile
from app.models.domain.projection import ProjectionConfig

logger = logging.getLogger(__name__)


class DefaultProjectionPolicy(ProjectionPolicyInterface):
    """Apply include/exclude/rename projection to a profile."""

    def project(self, profile: CanonicalProfile, config: ProjectionConfig) -> dict[str, Any]:
        data = profile.model_dump()

        if config.include_fields:
            unknown = set(config.include_fields) - set(data.keys())
            if unknown:
                raise ProjectionException(
                    message=f"Unknown fields in include_fields: {unknown}",
                    details={"unknown_fields": list(unknown)},
                )
            data = {k: v for k, v in data.items() if k in config.include_fields}

        elif config.exclude_fields:
            data = {k: v for k, v in data.items() if k not in config.exclude_fields}

        # Apply renames
        for old_name, new_name in config.rename_fields.items():
            if old_name in data:
                data[new_name] = data.pop(old_name)

        return data
