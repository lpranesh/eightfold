"""PDF Parser with fallback to OCR and Docling."""

import io
import tempfile
import pdfplumber
import pytesseract
from PIL import Image

from app.interfaces.parser import ParserInterface
from app.models.intermediate import ParsedDocument, SourceType
from app.core.exceptions import ParsingException
from app.core.config import settings


class PDFParser(ParserInterface):
    """Parses PDF resumes, with OCR fallback."""

    def can_parse(self, source_type: SourceType, file_extension: str) -> bool:
        return source_type == SourceType.RESUME_PDF or file_extension == ".pdf"

    def parse(self, content: bytes, source_type: SourceType, filename: str) -> ParsedDocument:
        try:
            text_pages = []
            warnings = []
            is_scanned = True

            # First attempt: direct text extraction using pdfplumber to check if selectable
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text and len(page_text.strip()) > 50:
                        is_scanned = False
                        text_pages.append(page_text)

            if is_scanned:
                # If scanned, automatically switch to Docling -> Tesseract OCR
                warnings.append("Document detected as scanned. Switching to Docling / OCR.")
                try:
                    from docling.document_converter import DocumentConverter
                    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
                        tmp.write(content)
                        tmp.flush()
                        converter = DocumentConverter()
                        result = converter.convert(tmp.name)
                        text_pages = [result.document.export_to_markdown()]
                except ImportError:
                    warnings.append("Docling not installed, falling back to pytesseract.")
                    text_pages = self._fallback_pytesseract(content, warnings)
                except Exception as e:
                    warnings.append(f"Docling conversion failed: {e}. Falling back to pytesseract.")
                    text_pages = self._fallback_pytesseract(content, warnings)

            full_text = "\n\n".join(text_pages)
            if not full_text.strip():
                raise ParsingException("Failed to extract any text from PDF.")

            return ParsedDocument(
                source_type=SourceType.RESUME_PDF,
                filename=filename,
                raw_text=full_text,
                parse_warnings=warnings,
            )
        except ParsingException:
            raise
        except Exception as e:
            raise ParsingException(f"Failed to parse PDF: {e}")
            
    def _fallback_pytesseract(self, content: bytes, warnings: list) -> list[str]:
        text_pages = []
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                try:
                    pil_img = page.to_image(resolution=200).original
                    ocr_text = pytesseract.image_to_string(pil_img)
                    if ocr_text and ocr_text.strip():
                        text_pages.append(ocr_text)
                except Exception as e:
                    warnings.append(f"OCR failed on a page: {e}")
        return text_pages
