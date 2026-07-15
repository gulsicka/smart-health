from fastapi import FastAPI
from app.consumer import start_consumer, stop_consumer, consume_events
from app.routers import analytics
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor


@asynccontextmanager
async def lifespan(app):
    await start_consumer() #everything before yield is "startup", creates and connects to kafka consumer
    import asyncio
    asyncio.create_task(consume_events())  # start consuming events in the background
    yield # fastapi lifespan pauses here and starts serving reqs, "the app is live"
    await stop_consumer() #shutdown


resource = Resource.create({"service.name": "analytics-service"})  
provider = TracerProvider(resource=resource)
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint="http://jaeger:4317", insecure=True)))
trace.set_tracer_provider(provider)

app = FastAPI(lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app)
Instrumentator().instrument(app).expose(app)

app.include_router(analytics.router)

@app.get("/health")
def health():
    return {"status": "ok", "service": "analytics-service"}