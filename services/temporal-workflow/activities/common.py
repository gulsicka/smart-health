from temporalio import activity
from schemas import FailedWorkflowInput


@activity.defn
async def failed_workflow(data: FailedWorkflowInput):
    print(f"Workflow failed: {data.error}")
