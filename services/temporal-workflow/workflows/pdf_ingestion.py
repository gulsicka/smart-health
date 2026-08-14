from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from activities.pdf_ingestion import extract_pdf_pages, get_existing_page_hashes, process_pdf_page, delete_pdf_page
    from schemas import PdfIngestionInput, PdfPageInput, PdfPageDeleteInput


@workflow.defn
class PdfIngestionWorkflow:
    @workflow.run
    async def run(self, data: PdfIngestionInput) -> dict:
        pages = await workflow.execute_activity(
            extract_pdf_pages,
            data,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        existing_hashes = await workflow.execute_activity(
            get_existing_page_hashes,
            data.source,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        seen_page_numbers = set()
        total_chunks = 0
        failed_pages = []

        for page in pages:
            page_number = page["page_number"]
            seen_page_numbers.add(page_number)

            if existing_hashes.get(str(page_number)) == page["page_hash"]:
                continue  #skip re embedding it

            try:
                chunks_stored = await workflow.execute_activity(
                    process_pdf_page,
                    PdfPageInput(source=data.source, page_number=page_number, text=page["text"], page_hash=page["page_hash"]),
                    start_to_close_timeout=timedelta(seconds=60),
                    retry_policy=RetryPolicy(maximum_attempts=3),
                )
                total_chunks += chunks_stored
            except Exception:
                failed_pages.append(page_number)

        orphaned = {int(k) for k in existing_hashes.keys()} - seen_page_numbers
        for page_number in orphaned:
            await workflow.execute_activity(
                delete_pdf_page,
                PdfPageDeleteInput(source=data.source, page_number=page_number),
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )

        return {"chunks_stored": total_chunks, "failed_pages": failed_pages}
