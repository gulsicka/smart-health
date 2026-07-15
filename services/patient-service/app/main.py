from fastapi import FastAPI
from app.routers import patient
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)

app.include_router(patient.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "patient-service"}
