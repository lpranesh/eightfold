"""Domain models for projection configuration.

Projections create customized output views of the canonical profile
without modifying the underlying data.
"""

from typing import Optional

from pydantic import BaseModel, Field, model_validator


class ProjectionConfig(BaseModel):
    """Configuration for projecting a candidate profile.

    Supports including/excluding fields, renaming fields, and hiding metadata.
    Validation ensures include_fields and exclude_fields are not used together.
    """

    include_fields: Optional[list[str]] = None
    exclude_fields: Optional[list[str]] = None
    rename_fields: dict[str, str] = Field(default_factory=dict)
    hide_metadata: bool = False

    @model_validator(mode="after")
    def validate_field_lists(self) -> "ProjectionConfig":
        """Ensure include_fields and exclude_fields are mutually exclusive."""
        if self.include_fields and self.exclude_fields:
            raise ValueError(
                "Cannot specify both include_fields and exclude_fields. "
                "Use one or the other."
            )
        return self
