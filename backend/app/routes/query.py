from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.core.security import get_current_user
from app.services.ingestion import search_similar_chunks
from openai import OpenAI
import os
import json

router = APIRouter()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You are a strict document question-answering assistant.

Rules:
1. Answer ONLY using the provided context.
2. If the answer is not explicitly found in the context, respond exactly with:
   "I cannot find this information in the document."
3. Do NOT use outside knowledge.
4. Keep answers concise and factual.
"""

class QueryRequest(BaseModel):
    question: str
    chat_history: list = []


@router.post("/query")
async def query_document(
    request: QueryRequest,
    current_user=Depends(get_current_user),
):

    # ==============================
    # 🔥 1️⃣ STRUCTURAL DETECTION
    # ==============================

    question_lower = request.question.lower()

    chunks_path = f"vector_store/{current_user.id}_chunks.json"

    if os.path.exists(chunks_path):
        with open(chunks_path, "r") as f:
            chunks = json.load(f)

        # Handle last line / last paragraph
        if "last line" in question_lower or "last paragraph" in question_lower:
            last_chunk = next((c for c in chunks if c.get("is_last")), None)
            if last_chunk:
                return {
                    "question": request.question,
                    "answer": last_chunk["text"],
                    "sources": [last_chunk["text"]]
                }

        # Handle first line / first paragraph
        if "first line" in question_lower or "first paragraph" in question_lower:
            first_chunk = next((c for c in chunks if c.get("is_first")), None)
            if first_chunk:
                return {
                    "question": request.question,
                    "answer": first_chunk["text"],
                    "sources": [first_chunk["text"]]
                }

    # ==============================
    # 🔥 2️⃣ NORMAL VECTOR SEARCH
    # ==============================

    results = search_similar_chunks(current_user.id, request.question)

    if not results:
        return {
            "question": request.question,
            "answer": "I cannot find this information in the document.",
            "sources": []
        }

    top_chunks = [r["chunk"] for r in results if "chunk" in r]
    context = "\n\n".join(top_chunks)

    # ==============================
    # 🔥 3️⃣ BUILD CHAT HISTORY
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
    # 🔥 4️⃣ CALL OPENAI
    # ==============================

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.1,
    )

    answer = response.choices[0].message.content.strip()

    return {
        "question": request.question,
        "answer": answer,
        "sources": top_chunks
    }