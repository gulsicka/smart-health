from fastapi import FastAPI
from app.routers import user, role
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)

app.include_router(user.router)
app.include_router(role.router)

@app.get("/health")
def health():
    return {"status": "ok", "service": "auth-service"}




