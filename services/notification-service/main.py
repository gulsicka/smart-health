from fastapi import FastAPI

import models  # noqa: F401  (Base.metadata.create_all runs on import)
from router import router

app = FastAPI(title="Notification Service")

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "notification-service"}
