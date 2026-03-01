import os
import json
from typing import List, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from openai import OpenAI

from app.core.security import get_current_user
from app.services.ingestion import search_similar_chunks

router = APIRouter()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

VECTOR_DIR = "vector_store"


# =========================
# SYSTEM PROMPT
# =========================

SYSTEM_PROMPT = """
You are a strict document question-answering assistant.

Rules:
1. Answer ONLY using the provided context.
2. If the answer is not explicitly found in the context, respond exactly with:
   "I cannot find this information in the document."
3. Do NOT use outside knowledge.
4. Keep answers concise and factual.
"""


# =========================
# REQUEST MODEL
# =========================

class QueryRequest(BaseModel):
    question: str
    document_id: str
    chat_history: List[Dict[str, str]] = Field(default_factory=list)


# =========================
# QUERY DOCUMENT
# =========================

@router.post("/query")
async def query_document(
    request: QueryRequest,
    current_user=Depends(get_current_user),
):

    user_id = current_user.id
    question_lower = request.question.lower()

    user_dir = f"{VECTOR_DIR}/{user_id}"
    chunks_json_path = f"{user_dir}/{request.document_id}_chunks.json"

    # ==============================
    # 1️⃣ STRUCTURAL DETECTION
    # ==============================

    if os.path.exists(chunks_json_path):

        with open(chunks_json_path, "r") as f:
            structured_chunks = json.load(f)

        # First line
        if "first line" in question_lower:
            first_chunk = next(
                (c for c in structured_chunks if c.get("is_first")),
                None
            )
            if first_chunk:
                return {
                    "question": request.question,
                    "answer": first_chunk["text"],
                    "sources": [first_chunk["text"]]
                }

        # Last line
        if "last line" in question_lower:
            last_chunk = next(
                (c for c in structured_chunks if c.get("is_last")),
                None
            )
            if last_chunk:
                return {
                    "question": request.question,
                    "answer": last_chunk["text"],
                    "sources": [last_chunk["text"]]
                }

    # ==============================
    # 2️⃣ VECTOR SEARCH
    # ==============================

    results = search_similar_chunks(
        user_id,
        request.document_id,
        request.question
    )

    if not results:
        return {
            "question": request.question,
            "answer": "I cannot find this information in the document.",
            "sources": []
        }

    top_chunks = [r["chunk"] for r in results if "chunk" in r]
    context = "\n\n".join(top_chunks)

    # ==============================
    # 3️⃣ BUILD CHAT HISTORY
    # ==============================

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    for msg in request.chat_history:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    messages.append({
        "role": "user",
        "content": f"""
Context:
{context}

Question:
{request.question}
"""
    })

    # ==============================
    # 4️⃣ CALL OPENAI
    # ==============================

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.1,
        )

        answer = response.choices[0].message.content.strip()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "question": request.question,
        "answer": answer,
        "sources": top_chunks
    }