import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from workflows import UserCreationWorkflow
from activities import create_patient_record

async def main():

    while True:
        # the worker was starting before temporal was ready, so we retry connection and wait for temporal to get ready
        try:
            client = await Client.connect("temporal:7233")
            break
        except Exception:
            print("Waiting for Temporal...")
            await asyncio.sleep(3)

    worker = Worker(
        client,
        task_queue="user_creation_queue",
        workflows=[UserCreationWorkflow],
        activities=[create_patient_record],
    )

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())