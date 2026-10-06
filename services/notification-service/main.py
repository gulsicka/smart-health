from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models  # noqa: F401  (Base.metadata.create_all runs on import)
from router import router

app = FastAPI(title="Notification Service", description="Per-user notifications: list and mark as read.", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # learners run their frontends on arbitrary origins; auth uses bearer tokens, not cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "notification-service"}
