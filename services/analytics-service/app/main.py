from fastapi import FastAPI
from app.consumer import start_consumer, stop_consumer, consume_events
from app.routers import analytics
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app):
    await start_consumer() #everything before yield is "startup", creates and connects to kafka consumer
    import asyncio
    asyncio.create_task(consume_events())  # start consuming events in the background
    yield # fastapi lifespan pauses here and starts serving reqs, "the app is live"
    await stop_consumer() #shutdown

app = FastAPI(lifespan=lifespan)

app.include_router(analytics.router)

@app.get("/health")
def health():
    return {"status": "ok", "service": "analytics-service"}