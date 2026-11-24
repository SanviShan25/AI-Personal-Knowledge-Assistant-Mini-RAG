"""Upload -> (background) pages -> chunks -> embeddings -> chunks table."""

import logging
import uuid
from pathlib import PurePath

from sqlalchemy import delete, insert, update
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import SessionLocal
from app.models.document import Chunk, Document, DocumentFile
from app.services import embeddings
from app.services.chunking import chunk_pages
from app.services.pdf import IngestionError, extract_pages
from app.services.retrieval import to_db_vector

log = logging.getLogger(__name__)


def display_name(filename: str | None) -> str:
    # Only used for display; nothing is ever written to disk under the client's filename.
    name = PurePath((filename or "").replace("\\", "/")).name.strip()
    return name[:255] or "document.pdf"


def create_document(db: Session, user_id: int, filename: str | None, data: bytes) -> Document:
    """Store the upload and mark it as processing. Cheap, so it runs inside the request."""
    if not data.startswith(b"%PDF"):
        raise IngestionError("File is not a valid PDF.")

    document = Document(
        id=str(uuid.uuid4()),
        user_id=user_id,
        filename=display_name(filename),
        size_bytes=len(data),
        status="processing",
    )
    db.add(document)
    db.add(DocumentFile(document_id=document.id, data=data))
    db.commit()
    return document


def process_document(document_id: str) -> None:
    """Parse, chunk and embed a stored document. Runs as a background task with its own session."""
    db = SessionLocal()
    try:
        file = db.get(DocumentFile, document_id)
        if file is None:  # deleted before processing started
            return
        pages = extract_pages(file.data)
        chunks = chunk_pages(pages, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
        if not chunks:
            raise IngestionError(
                "No readable text found. Scanned or image-only PDFs need OCR, which isn't supported yet."
            )

        vectors = embeddings.embed_documents([c.text for c in chunks])
        db.execute(delete(Chunk).where(Chunk.document_id == document_id))  # safe to re-run
        db.execute(
            insert(Chunk),
            [
                {
                    "document_id": document_id,
                    "chunk_index": c.chunk_index,
                    "page": c.page,
                    "text": c.text,
                    "embedding": to_db_vector(v),
                }
                for c, v in zip(chunks, vectors)
            ],
        )
        db.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(status="ready", error=None, num_pages=len(pages), num_chunks=len(chunks))
        )
        db.commit()
    except IngestionError as exc:
        db.rollback()
        _mark_failed(db, document_id, str(exc))
    except Exception:
        log.exception("Processing document %s failed", document_id)
        db.rollback()
        _mark_failed(db, document_id, "Processing failed unexpectedly. Try again.")
    finally:
        db.close()


def _mark_failed(db: Session, document_id: str, message: str) -> None:
    db.execute(update(Document).where(Document.id == document_id).values(status="failed", error=message[:500]))
    db.commit()


def fail_interrupted_documents() -> None:
    """At startup, anything still 'processing' was cut off by a restart."""
    with SessionLocal() as db:
        db.execute(
            update(Document)
            .where(Document.status == "processing")
            .values(status="failed", error="Processing was interrupted. Click retry.")
        )
        db.commit()
