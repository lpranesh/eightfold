"""Deterministic data normalization."""

import re
from app.models.intermediate import ExtractedValue


class Normalizer:
    """Applies deterministic normalizations based on field names."""

    PHONE_RE = re.compile(r"[^\d+]")

    @classmethod
    def normalize(cls, value: ExtractedValue) -> ExtractedValue:
        """Normalize the extracted value based on its field name."""
        raw = value.raw_value
        if raw is None:
            return value

        if value.field_name == "email" and isinstance(raw, str):
            value.raw_value = raw.lower().strip()
        
        elif value.field_name == "phone" and isinstance(raw, str):
            # E.164 approximation: strip non-digits, ensure + prefix if country code exists
            digits = cls.PHONE_RE.sub("", raw)
            if len(digits) > 10 and not digits.startswith("+"):
                digits = "+" + digits
            value.raw_value = digits
            
        elif value.field_name in ["full_name", "first_name", "last_name", "current_title", "current_company", "location"] and isinstance(raw, str):
            # Whitespace cleanup
            value.raw_value = " ".join(raw.split())
            
        elif value.field_name in ["linkedin_url", "github_url", "portfolio_url"] and isinstance(raw, str):
            # URL normalization
            url = raw.strip()
            if url and not url.startswith("http"):
                url = "https://" + url
            value.raw_value = url

        return value
