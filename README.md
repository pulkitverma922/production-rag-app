# RAG Pipeline — FastAPI + Pinecone + OpenAI

End-to-end Retrieval-Augmented Generation pipeline. Upload PDF/DOCX files, then ask natural language questions against them.

---

## Stack

| Layer | Technology |
|---|---|
| API | FastAPI |
| Document Loading | PyMuPDF (PDF), python-docx (DOCX) |
| Chunking | Fixed-size (500 tokens, 50 overlap) |
| Embeddings | OpenAI `text-embedding-3-small` |
| Vector Store | Pinecone (serverless, cosine similarity) |
| Generation | OpenAI `gpt-4o` |

---

## Project Structure

```
rag_pipeline/
├── main.py                     # FastAPI app entry point
├── requirements.txt
├── .env.example                # Copy to .env and fill in keys
└── app/
    ├── core/
    │   ├── config.py           # Settings from .env
    │   ├── document_loader.py  # PDF + DOCX loaders
    │   ├── chunker.py          # Fixed-size text chunker
    │   ├── embedder.py         # OpenAI embedding calls
    │   ├── vector_store.py     # Pinecone upsert + search
    │   └── generator.py        # GPT-4o answer generation
    └── routers/
        ├── ingest.py           # POST /api/v1/ingest/upload
        └── query.py            # POST /api/v1/query/ask
```

---

## Setup

### 1. Clone and install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your OpenAI and Pinecone API keys
```

### 3. Run the server

```bash
uvicorn main:app --reload --port 8000
```

### 4. Open interactive docs

Visit `http://localhost:8000/docs` for the Swagger UI.

---

## API Usage

### Upload documents

```bash
curl -X POST http://localhost:8000/api/v1/ingest/upload \
  -F "files=@report.pdf" \
  -F "files=@contract.docx"
```

**Response:**
```json
{
  "results": [
    {
      "filename": "report.pdf",
      "status": "success",
      "chunks_created": 42,
      "vectors_upserted": 42
    }
  ]
}
```

### Ask a question

```bash
curl -X POST http://localhost:8000/api/v1/query/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the key findings in the report?"}'
```

**Response:**
```json
{
  "question": "What are the key findings in the report?",
  "answer": "Based on the documents, the key findings are...",
  "sources": ["report.pdf"],
  "chunks_used": 5,
  "model": "gpt-4o",
  "usage": {
    "prompt_tokens": 820,
    "completion_tokens": 210,
    "total_tokens": 1030
  }
}
```

### Filter by source document

```bash
curl -X POST http://localhost:8000/api/v1/query/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Summarize the contract terms", "source_filter": "contract.docx"}'
```

---

## How It Works

```
INGEST PIPELINE
───────────────
Upload File → Extract Text → Chunk (500 tokens) → Embed (OpenAI) → Store (Pinecone)

QUERY PIPELINE
──────────────
User Question → Embed Query → Search Pinecone (top-5) → Build Context → GPT-4o → Answer
```

---

## Customization

| Setting | Default | Where to change |
|---|---|---|
| Chunk size | 500 tokens | `CHUNK_SIZE` in `.env` |
| Chunk overlap | 50 tokens | `CHUNK_OVERLAP` in `.env` |
| Results returned | 5 | `TOP_K` in `.env` |
| Embedding model | text-embedding-3-small | `OPENAI_EMBED_MODEL` in `.env` |
| Chat model | gpt-4o | `OPENAI_CHAT_MODEL` in `.env` |
| Pinecone index | rag-index | `PINECONE_INDEX_NAME` in `.env` |
