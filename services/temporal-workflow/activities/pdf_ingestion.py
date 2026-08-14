from temporalio import activity
import clients.ai.api as ai_client
from schemas import PdfIngestionInput, PdfPageInput, PdfPageDeleteInput


@activity.defn
async def extract_pdf_pages(data: PdfIngestionInput) -> list:
    return await ai_client.extract_pdf_pages(data.source, data.pdf_base64)


@activity.defn
async def get_existing_page_hashes(source: str) -> dict:
    return await ai_client.get_page_hashes(source)


@activity.defn
async def process_pdf_page(data: PdfPageInput) -> int:
    return await ai_client.process_pdf_page(data.source, data.page_number, data.text, data.page_hash)


@activity.defn
async def delete_pdf_page(data: PdfPageDeleteInput):
    await ai_client.delete_pdf_page(data.source, data.page_number)
