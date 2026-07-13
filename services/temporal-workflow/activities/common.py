from temporalio import activity


@activity.defn
async def failed_workflow(data: dict):
    print(f"Workflow failed: {data.get('error')}")
