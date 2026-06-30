"""PDF Parser with fallback to OCR."""

import io
import pdfplumber
import pytesseract
from PIL import Image

from app.interfaces.parser import ParserInterface
from app.models.intermediate import ParsedContent, SourceType
from app.core.exceptions import ParsingException
from app.core.config import settings


class PDFParser(ParserInterface):
    """Parses PDF resumes, with OCR fallback."""

    def can_parse(self, source_type: SourceType, file_extension: str) -> bool:
        return source_type == SourceType.RESUME_PDF or file_extension == ".pdf"

    def parse(self, content: bytes, source_type: SourceType, filename: str) -> ParsedContent:
        try:
            text_pages = []
            warnings = []

            # First attempt: direct text extraction using pdfplumber
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text_pages.append(page_text)
                    else:
                        # Fallback to OCR if no text found on page
                        if settings.OCR_ENGINE == "tesseract":
                            try:
                                pil_img = page.to_image(resolution=200).original
                                ocr_text = pytesseract.image_to_string(pil_img)
                                if ocr_text and ocr_text.strip():
                                    text_pages.append(ocr_text)
                            except Exception as e:
                                warnings.append(f"OCR failed on a page: {e}")
                        else:
                            warnings.append(f"No text on page and OCR disabled/unavailable.")

            full_text = "\n\n".join(text_pages)
            if not full_text.strip():
                raise ParsingException("Failed to extract any text from PDF.")

            return ParsedContent(
                source_type=SourceType.RESUME_PDF,
                filename=filename,
                raw_text=full_text,
                parse_warnings=warnings,
            )
        except ParsingException:
            raise
        except Exception as e:
            raise ParsingException(f"Failed to parse PDF: {e}")
