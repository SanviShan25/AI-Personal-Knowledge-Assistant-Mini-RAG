import os
import json
import uuid
import faiss
import numpy as np
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

# =========================
# LOAD EMBEDDING MODEL
# =========================

model = SentenceTransformer("all-MiniLM-L6-v2")

VECTOR_DIR = "vector_store"
os.makedirs(VECTOR_DIR, exist_ok=True)


# =========================
# PROCESS DOCUMENT
# =========================

async def process_document(file, user_id: int):

    # Create unique document ID
    document_id = str(uuid.uuid4())

    # Create user directory
    user_dir = f"{VECTOR_DIR}/{user_id}"
    os.makedirs(user_dir, exist_ok=True)

    # Save uploaded file
    file_path = f"{user_dir}/{document_id}_{file.filename}"

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Extract text from PDF
    reader = PdfReader(file_path)

    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"

    # Validate text
    if not text.strip():
        raise ValueError("PDF contains no readable text")

    # Chunk text (line-based for structural precision)
    chunks = chunk_text(text)

    if not chunks:
        raise ValueError("No text extracted from PDF")

    # Create embeddings
    embeddings = model.encode(chunks)

    # Store embeddings and metadata
    store_embeddings(user_dir, document_id, embeddings, chunks)

    return {
        "message": "Document processed successfully",
        "document_id": document_id,
        "filename": file.filename
    }


# =========================
# CHUNK TEXT (Line-Based)
# =========================

def chunk_text(text):

    raw_lines = text.split("\n")

    # Remove empty lines
    lines = [line.strip() for line in raw_lines if line.strip()]

    return lines


# =========================
# STORE EMBEDDINGS
# =========================

def store_embeddings(user_dir, document_id, embeddings, chunks):

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)

    index.add(np.array(embeddings))

    # Save FAISS index
    faiss.write_index(index, f"{user_dir}/{document_id}.index")

    # Save raw chunks for search
    np.save(f"{user_dir}/{document_id}_chunks.npy", np.array(chunks))

    # Save structured metadata
    structured_chunks = []

    for i, chunk in enumerate(chunks):
        structured_chunks.append({
            "text": chunk,
            "is_first": i == 0,
            "is_last": i == len(chunks) - 1
        })

    with open(f"{user_dir}/{document_id}_chunks.json", "w") as f:
        json.dump(structured_chunks, f)


# =========================
# SEARCH SIMILAR CHUNKS
# =========================

def search_similar_chunks(user_id: int, document_id: str, query: str, top_k: int = 3):

    user_dir = f"{VECTOR_DIR}/{user_id}"

    index_path = f"{user_dir}/{document_id}.index"
    chunks_path = f"{user_dir}/{document_id}_chunks.npy"

    if not os.path.exists(index_path) or not os.path.exists(chunks_path):
        return []

    index = faiss.read_index(index_path)
    chunks = np.load(chunks_path, allow_pickle=True)

    query_embedding = model.encode([query])

    distances, indices = index.search(np.array(query_embedding), top_k)

    results = []

    for i, idx in enumerate(indices[0]):
        results.append({
            "chunk": chunks[idx],
            "score": float(distances[0][i])
        })

    return results