from fastapi import FastAPI
from app.routers import department, clinic, provider, availability
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)

app.include_router(department.router)
app.include_router(clinic.router)
app.include_router(provider.router)
app.include_router(availability.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "provider-service"}
