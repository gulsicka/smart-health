from fastapi import FastAPI
from app.routers import patient

app = FastAPI()

app.include_router(patient.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "patient-service"}
