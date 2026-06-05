import uuid
from typing import List, Dict, Any
from pinecone import Pinecone, ServerlessSpec
from app.core.config import settings

pc = Pinecone(api_key=settings.PINECONE_API_KEY)

# sentence-transformers all-MiniLM-L6-v2 outputs 384 dimensions (NOT 1536)
EMBEDDING_DIMENSION = 384


def get_or_create_index():
    existing = [idx.name for idx in pc.list_indexes()]
    if settings.PINECONE_INDEX_NAME not in existing:
        print(f"Creating Pinecone index '{settings.PINECONE_INDEX_NAME}' with dim={EMBEDDING_DIMENSION}...")
        pc.create_index(
            name=settings.PINECONE_INDEX_NAME,
            dimension=EMBEDDING_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(
                cloud=settings.PINECONE_CLOUD,
                region=settings.PINECONE_REGION,
            ),
        )
        print("Pinecone index created.")
    return pc.Index(settings.PINECONE_INDEX_NAME)


def upsert_vectors(chunks: List[Dict[str, Any]], embeddings: List[List[float]]) -> int:
    index = get_or_create_index()
    vectors = []
    for chunk, embedding in zip(chunks, embeddings):
        vectors.append({
            "id": str(uuid.uuid4()),
            "values": embedding,
            "metadata": {
                **chunk["metadata"],
                "text": chunk["text"],
            },
        })
    # Pinecone recommends batches of 100
    for i in range(0, len(vectors), 100):
        index.upsert(vectors=vectors[i:i+100])
    return len(vectors)


def similarity_search(
    query_embedding: List[float],
    top_k: int = None,
    filter: Dict = None,
) -> List[Dict[str, Any]]:
    top_k = top_k or settings.TOP_K
    index = get_or_create_index()
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
        filter=filter,
    )
    return [
        {
            "id": m.id,
            "score": m.score,
            "text": m.metadata.get("text", ""),
            "source": m.metadata.get("source", ""),
            "chunk_index": m.metadata.get("chunk_index", 0),
        }
        for m in results.matches
    ]


def list_indexed_sources() -> list:
    """Fetch all unique source filenames stored in Pinecone."""
    try:
        index = get_or_create_index()
        # Query with a dummy zero vector to get sample metadata
        dummy = [0.0] * EMBEDDING_DIMENSION
        results = index.query(vector=dummy, top_k=100, include_metadata=True)
        sources = {}
        for match in results.matches:
            src = match.metadata.get("source", "")
            if src and src not in sources:
                sources[src] = {
                    "filename": src,
                    "chunks": match.metadata.get("total_chunks", "?"),
                }
        return list(sources.values())
    except Exception:
        return []