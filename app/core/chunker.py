from typing import List
from app.core.config import settings


def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
    """
    Split text into fixed-size token-approximate chunks with overlap.
    Uses word-level splitting as a proxy for tokens (~0.75 words per token).
    """
    chunk_size = chunk_size or settings.CHUNK_SIZE
    overlap = overlap or settings.CHUNK_OVERLAP

    # Convert token counts to approximate word counts
    word_chunk_size = int(chunk_size * 0.75)
    word_overlap = int(overlap * 0.75)

    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + word_chunk_size
        chunk_words = words[start:end]
        chunk = " ".join(chunk_words).strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(words):
            break
        start = end - word_overlap  # slide back by overlap

    return chunks


def chunk_documents(text: str, source_name: str) -> List[dict]:
    """
    Chunk text and attach metadata to each chunk.
    Returns list of dicts with 'text' and 'metadata'.
    """
    chunks = chunk_text(text)
    return [
        {
            "text": chunk,
            "metadata": {
                "source": source_name,
                "chunk_index": i,
                "total_chunks": len(chunks),
            },
        }
        for i, chunk in enumerate(chunks)
    ]
