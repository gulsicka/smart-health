from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routers import ingest, retrieve
from app.database import init_db
from prometheus_fastapi_instrumentator import Instrumentator
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

resource = Resource.create({"service.name": "ai-service"})
otel_provider = TracerProvider(resource=resource)
otel_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint="http://jaeger:4317", insecure=True)))
trace.set_tracer_provider(otel_provider)


@asynccontextmanager
async def lifespan(app):
    init_db()  # create vector extension + tables on startup
    yield


app = FastAPI(lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app, excluded_urls="/metrics")
Instrumentator().instrument(app).expose(app)

app.include_router(ingest.router)
app.include_router(retrieve.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-service"}
