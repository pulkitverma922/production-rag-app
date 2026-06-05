import io
from typing import List
from fastapi import UploadFile
import fitz  # PyMuPDF
from docx import Document


async def load_pdf(file: UploadFile) -> str:
    """Extract all text from a PDF file."""
    contents = await file.read()
    pdf = fitz.open(stream=contents, filetype="pdf")
    text_parts = []
    for page_num in range(len(pdf)):
        page = pdf[page_num]
        text = page.get_text("text")
        if text.strip():
            text_parts.append(f"[Page {page_num + 1}]\n{text.strip()}")
    pdf.close()
    return "\n\n".join(text_parts)


async def load_docx(file: UploadFile) -> str:
    """Extract all text from a DOCX file."""
    contents = await file.read()
    doc = Document(io.BytesIO(contents))
    paragraphs = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
    return "\n\n".join(paragraphs)


async def load_document(file: UploadFile) -> str:
    """Route to correct loader based on file extension."""
    filename = file.filename.lower()
    if filename.endswith(".pdf"):
        return await load_pdf(file)
    elif filename.endswith(".docx"):
        return await load_docx(file)
    else:
        raise ValueError(f"Unsupported file type: {file.filename}. Only PDF and DOCX are supported.")
