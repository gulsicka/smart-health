from fastapi import FastAPI
from contextlib import asynccontextmanager
from app import kafka_producer
from app.routers import appointment

@asynccontextmanager
async def lifespan(app):
    await kafka_producer.start_producer() #everything before yield is "startup", creates and connects to kafka producer
    yield # fastapi lifespan pauses here and starts serving reqs, "the app is live"
    await kafka_producer.stop_producer() #shutdown

app = FastAPI(lifespan=lifespan)

app.include_router(appointment.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "appointment-service"}
