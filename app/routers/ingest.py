from fastapi import APIRouter, UploadFile, File
from typing import List, Annotated
import traceback
from app.core.document_loader import load_document
from app.core.chunker import chunk_documents
from app.core.embedder import embed_texts
from app.core.vector_store import upsert_vectors

router = APIRouter()


@router.post("/upload")
async def upload_documents(
    files: Annotated[List[UploadFile], File(description="Upload PDF or DOCX files")]
):
    results = []

    for file in files:
        try:
            # Step 1: Load
            text = await load_document(file)
            if not text.strip():
                results.append({"filename": file.filename, "status": "skipped", "reason": "No text found"})
                continue

            # Step 2: Chunk
            chunks = chunk_documents(text, source_name=file.filename)

            # Step 3: Embed
            texts = [c["text"] for c in chunks]
            embeddings = await embed_texts(texts)

            # Step 4: Upsert
            upserted = upsert_vectors(chunks, embeddings)

            results.append({
                "filename": file.filename,
                "status": "success",
                "chunks_created": len(chunks),
                "vectors_upserted": upserted,
            })

        except Exception as e:
            tb = traceback.format_exc()
            print("\n" + "="*60)
            print(f"UPLOAD ERROR --- {file.filename}")
            print(tb)
            print("="*60 + "\n")
            results.append({
                "filename": file.filename,
                "status": "error",
                "reason": str(e),
            })

    return {"results": results}