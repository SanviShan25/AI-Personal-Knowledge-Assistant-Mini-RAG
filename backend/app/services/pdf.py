"""PDF text extraction, kept free of database imports so scripts can use it on their own."""

import io
import logging

from pypdf import PdfReader

log = logging.getLogger(__name__)


class IngestionError(Exception):
    """A user-facing problem with the uploaded file."""


def extract_pages(data: bytes) -> list[str]:
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted and not reader.decrypt(""):
            raise IngestionError("Password-protected PDFs are not supported.")
        return [page.extract_text() or "" for page in reader.pages]
    except IngestionError:
        raise
    except Exception as exc:  # pypdf raises many different error types on broken files
        log.info("Could not parse PDF: %s", exc)
        raise IngestionError("Could not read this PDF. It may be corrupted.") from exc
