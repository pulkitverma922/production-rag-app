from typing import List, Dict, Any
from groq import AsyncGroq
from app.core.config import settings

client = AsyncGroq(api_key=settings.GROQ_API_KEY)

SYSTEM_PROMPT = """You are a helpful assistant that answers questions based strictly on the provided context.

Rules:
- Only use information from the context below to answer.
- If the answer is not in the context, say "I don't have enough information to answer this based on the provided documents."
- Be concise and accurate.
- Cite the source document when possible.
"""


def build_context(chunks: List[Dict[str, Any]]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(f"[{i}] Source: {chunk['source']} (chunk {chunk['chunk_index']})\n{chunk['text']}")
    return "\n\n---\n\n".join(parts)


async def generate_answer(query: str, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    context = build_context(chunks)
    user_message = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"

    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # current free Groq model
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
        max_tokens=1024,
    )

    answer = response.choices[0].message.content.strip()
    sources = list({chunk["source"] for chunk in chunks})

    return {
        "answer": answer,
        "sources": sources,
        "chunks_used": len(chunks),
        "model": "llama-3.3-70b-versatile (Groq)",
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        },
    }