from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import traceback
from app.core.embedder import embed_query
from app.core.vector_store import similarity_search, list_indexed_sources
from app.core.generator import generate_answer

router = APIRouter()


class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5
    source_filter: Optional[str] = None


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: list
    chunks_used: int
    model: str
    usage: dict


@router.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    if not request.question.strip():
        return QueryResponse(
            question=request.question,
            answer="Please enter a question.",
            sources=[], chunks_used=0, model="N/A", usage={}
        )

    try:
        query_embedding = await embed_query(request.question)

        pinecone_filter = None
        if request.source_filter:
            pinecone_filter = {"source": {"$eq": request.source_filter}}

        chunks = similarity_search(
            query_embedding=query_embedding,
            top_k=request.top_k,
            filter=pinecone_filter,
        )

        if not chunks:
            return QueryResponse(
                question=request.question,
                answer="No relevant documents found. Please upload documents first.",
                sources=[], chunks_used=0, model="N/A", usage={}
            )

        result = await generate_answer(request.question, chunks)
        return QueryResponse(question=request.question, **result)

    except Exception as e:
        tb = traceback.format_exc()
        print("\n" + "="*60)
        print("QUERY ERROR:", request.question)
        print(tb)
        print("="*60 + "\n")
        return QueryResponse(
            question=request.question,
            answer=f"Error: {str(e)}",
            sources=[], chunks_used=0, model="N/A", usage={}
        )


@router.get("/sources")
def get_sources():
    """Return all unique document sources stored in Pinecone — used to restore sidebar on page reload."""
    try:
        sources = list_indexed_sources()
        return {"sources": sources}
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return {"sources": [], "error": str(e)}