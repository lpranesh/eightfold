"""Data standardizer/normalizer."""

import re
from app.models.intermediate import ExtractedValue


class Normalizer:
    """Deterministically formats fields."""

    @classmethod
    def normalize(cls, value: ExtractedValue) -> ExtractedValue:
        """Apply formatting and track normalizations."""
        if not value.raw_value:
            return value

        original = value.raw_value
        applied = []
        
        # Email
        if value.field_name in ("email", "emails") and isinstance(original, str):
            value.raw_value = original.lower().strip()
            if original != value.raw_value:
                applied.append("Lowercase & Trim Whitespace")
            else:
                applied.append("Normalization attempted (No changes required)")
                
        # Phone
        elif value.field_name in ("phone", "phones") and isinstance(original, str):
            # Extract digits, keep leading +
            plus = "+" if original.startswith("+") else ""
            digits = re.sub(r'\D', '', original)
            value.raw_value = f"{plus}{digits}"
            if original != value.raw_value:
                applied.append("E.164 Formatting")
            else:
                applied.append("Normalization attempted (No changes required)")
                
        # URLs
        elif "url" in value.field_name and isinstance(original, str):
            if not original.startswith("http"):
                value.raw_value = f"https://{original}"
                applied.append("Added https scheme")
            else:
                applied.append("Normalization attempted (No changes required)")
                
        # Dates (YYYY-MM)
        elif value.field_name in ("start_date", "end_date", "graduation_year"):
            # A simplistic date normalizer for the assignment
            # E.g. "May 2020" -> "2020-05"
            val = str(original)
            months = {"jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05", "jun": "06", 
                      "jul": "07", "aug": "08", "sep": "09", "oct": "10", "nov": "11", "dec": "12"}
            for m, num in months.items():
                if m in val.lower():
                    year_match = re.search(r'\d{4}', val)
                    if year_match:
                        value.raw_value = f"{year_match.group(0)}-{num}"
                        applied.append("Standardized to YYYY-MM")
                        break
            if not applied:
                applied.append("Normalization attempted (No changes required)")
                
        # Strings (Whitespace cleanup)
        elif isinstance(original, str):
            value.raw_value = re.sub(r'\s+', ' ', original).strip()
            if original != value.raw_value:
                applied.append("Whitespace cleanup")
            else:
                applied.append("Normalization attempted (No changes required)")

        value.normalizations = applied
        return value
