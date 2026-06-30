"""PDF parser using pdfplumber with pytesseract OCR fallback.

Extracts text from PDF resume files. If pdfplumber fails to extract
meaningful text (e.g., scanned documents), falls back to OCR.
"""

import logging
from typing import Optional

from app.exceptions import ParsingException
from app.interfaces import ParserInterface
from app.models.domain.enums import SourceType
from app.models.domain.source import ParsedContent

logger = logging.getLogger(__name__)


class PDFParser(ParserInterface):
    """Parser for PDF resume files.

    Uses pdfplumber for native text extraction and pytesseract
    as an OCR fallback for scanned documents.
    """

    MIN_TEXT_LENGTH = 50  # Below this, we suspect a scanned PDF

    def __init__(self, ocr_enabled: bool = True) -> None:
        self._ocr_enabled = ocr_enabled

    def can_parse(self, source_type: SourceType, file_extension: str) -> bool:
        """Check if this parser handles the given source."""
        return file_extension.lower() == ".pdf"

    def parse(self, content: bytes, source_type: SourceType) -> ParsedContent:
        """Parse a PDF file into text content.

        Args:
            content: Raw PDF bytes.
            source_type: The source type (typically RESUME).

        Returns:
            ParsedContent with extracted text.

        Raises:
            ParsingException: If PDF parsing fails completely.
        """
        warnings: list[str] = []
        text = self._extract_with_pdfplumber(content, warnings)

        page_count = self._count_pages(content)

        if text and len(text.strip()) >= self.MIN_TEXT_LENGTH:
            logger.info(
                "PDF parsed successfully with pdfplumber",
                extra={"text_length": len(text), "pages": page_count},
            )
            return ParsedContent(
                source_type=source_type,
                raw_text=text,
                page_count=page_count,
                parse_warnings=warnings,
                metadata={"parser": "pdfplumber"},
            )

        # Fallback to OCR
        if self._ocr_enabled:
            logger.info("pdfplumber extracted insufficient text, falling back to OCR")
            ocr_text = self._extract_with_ocr(content, warnings)
            if ocr_text:
                return ParsedContent(
                    source_type=source_type,
                    raw_text=ocr_text,
                    page_count=page_count,
                    parse_warnings=warnings,
                    metadata={"parser": "pytesseract_ocr"},
                )

        if text:
            warnings.append(
                "Extracted text is very short; document may be partially scanned"
            )
            return ParsedContent(
                source_type=source_type,
                raw_text=text,
                page_count=page_count,
                parse_warnings=warnings,
                metadata={"parser": "pdfplumber", "quality": "low"},
            )

        raise ParsingException(
            message="Could not extract text from PDF",
            details={"warnings": warnings},
        )

    def _extract_with_pdfplumber(
        self, content: bytes, warnings: list[str]
    ) -> Optional[str]:
        """Extract text using pdfplumber."""
        try:
            import io

            import pdfplumber

            pages_text: list[str] = []
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        pages_text.append(page_text)
                    else:
                        warnings.append(f"Page {i + 1}: no text extracted")

            return "\n\n".join(pages_text) if pages_text else None
        except Exception as exc:
            logger.warning("pdfplumber extraction failed", exc_info=exc)
            warnings.append(f"pdfplumber failed: {exc}")
            return None

    def _extract_with_ocr(
        self, content: bytes, warnings: list[str]
    ) -> Optional[str]:
        """Extract text using pytesseract OCR fallback."""
        try:
            import io

            from pdf2image import convert_from_bytes
            from pytesseract import image_to_string

            images = convert_from_bytes(content)
            pages_text: list[str] = []
            for i, image in enumerate(images):
                text = image_to_string(image)
                if text.strip():
                    pages_text.append(text)
                else:
                    warnings.append(f"OCR page {i + 1}: no text recognized")

            return "\n\n".join(pages_text) if pages_text else None
        except ImportError:
            warnings.append(
                "OCR fallback unavailable: pytesseract or pdf2image not installed"
            )
            return None
        except Exception as exc:
            logger.warning("OCR extraction failed", exc_info=exc)
            warnings.append(f"OCR failed: {exc}")
            return None

    def _count_pages(self, content: bytes) -> Optional[int]:
        """Count pages in a PDF document."""
        try:
            import io

            import pdfplumber

            with pdfplumber.open(io.BytesIO(content)) as pdf:
                return len(pdf.pages)
        except Exception:
            return None
