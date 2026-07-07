from fastapi import FastAPI
from app.routers import user, role

app = FastAPI()

app.include_router(user.router)
app.include_router(role.router)

@app.get("/health")
def health():
    return {"status": "ok", "service": "auth-service"}




