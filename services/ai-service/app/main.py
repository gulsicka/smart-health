import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routers import ingest, retrieve, chat, communication, report
from app.database import init_db
from app import kafka_consumer
from prometheus_fastapi_instrumentator import Instrumentator
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.langchain import LangchainInstrumentor

resource = Resource.create({"service.name": "ai-service"})
otel_provider = TracerProvider(resource=resource)
otel_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint="http://jaeger:4317", insecure=True)))
trace.set_tracer_provider(otel_provider)


@asynccontextmanager
async def lifespan(app):
    init_db()
    await kafka_consumer.start_consumer()
    asyncio.create_task(kafka_consumer.consume_events())
    yield
    await kafka_consumer.stop_consumer()


app = FastAPI(lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app, excluded_urls="/metrics")
LangchainInstrumentor().instrument()  # auto-wraps every ChatGroq call (chat.py, communication.py, report.py) with its own span — model, tokens, latency, errors
Instrumentator().instrument(app).expose(app)

app.include_router(ingest.router)
app.include_router(retrieve.router)
app.include_router(chat.router)
app.include_router(communication.router)
app.include_router(report.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-service"}
