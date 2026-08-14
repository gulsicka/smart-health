from fastapi import APIRouter
from sqlalchemy.orm import Session
from fastapi import Depends
from app import schemas, crud
from app.database import get_db
from langchain_text_splitters import RecursiveCharacterTextSplitter
import fitz  # pymupdf
import pymupdf4llm
import hashlib
import base64

router = APIRouter()


@router.post("/internal/pdf/extract", response_model=schemas.PdfExtractResponse)
def extract_pdf(body: schemas.PdfExtractRequest):
    pdf_bytes = base64.b64decode(body.pdf_base64)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = pymupdf4llm.to_markdown(doc, page_chunks=True)

    result = []
    for page in pages:
        page_number = page["metadata"]["page_number"]
        page_hash = hashlib.md5(page["text"].encode()).hexdigest()
        result.append(schemas.PdfPage(page_number=page_number, text=page["text"], page_hash=page_hash))

    return schemas.PdfExtractResponse(pages=result)


@router.get("/internal/pdf/page-hashes", response_model=schemas.PageHashesResponse)
def page_hashes(source: str, db: Session = Depends(get_db)):
    return schemas.PageHashesResponse(page_hashes=crud.get_page_hashes(db, source))


@router.post("/internal/pdf/page", response_model=schemas.PdfPageResponse)
def ingest_page(body: schemas.PdfPageRequest, db: Session = Depends(get_db)):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(body.text)
    crud.replace_page_chunks(db, body.source, body.page_number, chunks, body.page_hash)
    return schemas.PdfPageResponse(chunks_stored=len(chunks))


@router.post("/internal/pdf/delete-page")
def delete_page(body: schemas.PdfPageDeleteRequest, db: Session = Depends(get_db)):
    crud.delete_chunks_for_page(db, body.source, body.page_number)
    return {"message": "deleted"}
