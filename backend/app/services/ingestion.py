import os
import faiss
import numpy as np
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

# Load embedding model once
model = SentenceTransformer("all-MiniLM-L6-v2")

VECTOR_DIR = "vector_store"
os.makedirs(VECTOR_DIR, exist_ok=True)


# =========================
# PROCESS DOCUMENT
# =========================
async def process_document(file, user_id: int):

    # Save file
    file_path = f"{VECTOR_DIR}/{user_id}_{file.filename}"

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Extract text
    reader = PdfReader(file_path)

    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted

    # Validate text
    if not text.strip():
        raise ValueError("PDF contains no readable text")

    # Chunk text
    chunks = chunk_text(text)

    if not chunks:
        raise ValueError("No text extracted from PDF")

    # Create embeddings
    embeddings = model.encode(chunks)

    # Store embeddings + chunks
    store_embeddings(user_id, embeddings, chunks)

    return {"message": "Document processed successfully"}


# =========================
# CHUNK TEXT
# =========================
def chunk_text(text, chunk_size=500):
    chunks = []

    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])

    return chunks


# =========================
# STORE EMBEDDINGS
# =========================
import json


def store_embeddings(user_id, embeddings, chunks):

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)

    index.add(np.array(embeddings))

    # Save FAISS index
    faiss.write_index(index, f"{VECTOR_DIR}/{user_id}.index")

    # Save chunks (numpy version for FAISS search)
    np.save(f"{VECTOR_DIR}/{user_id}_chunks.npy", np.array(chunks))

    # 🔥 NEW: Save structured metadata JSON
    structured_chunks = []

    for i, chunk in enumerate(chunks):
        structured_chunks.append({
            "chunk_id": i,
            "text": chunk,
            "is_first": i == 0,
            "is_last": i == len(chunks) - 1
        })

    with open(f"{VECTOR_DIR}/{user_id}_chunks.json", "w") as f:
        json.dump(structured_chunks, f, indent=2)


# =========================
# SEARCH SIMILAR CHUNKS
# =========================
def search_similar_chunks(user_id: int, query: str, top_k: int = 3):

    index_path = f"vector_store/{user_id}.index"
    chunks_path = f"vector_store/{user_id}_chunks.npy"

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