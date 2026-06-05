from typing import List
from sentence_transformers import SentenceTransformer

# Loads once on startup, cached in memory after that
# all-MiniLM-L6-v2: fast, free, 384-dim, great for RAG
_model = None

def get_model():
    global _model
    if _model is None:
        print("Loading embedding model (first time only, ~30 seconds)...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print("Embedding model ready.")
    return _model


async def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed a list of texts locally using sentence-transformers."""
    model = get_model()
    cleaned = [t.replace("\n", " ") for t in texts]
    embeddings = model.encode(cleaned, show_progress_bar=False, batch_size=32)
    return embeddings.tolist()


async def embed_query(query: str) -> List[float]:
    """Embed a single query string."""
    result = await embed_texts([query])
    return result[0]