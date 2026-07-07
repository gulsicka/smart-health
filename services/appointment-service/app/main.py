from fastapi import FastAPI
from app.routers import appointment

app = FastAPI()

app.include_router(appointment.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "appointment-service"}
