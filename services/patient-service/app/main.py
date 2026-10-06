import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app import kafka_producer, kafka_consumer
from app.routers import patient
from prometheus_fastapi_instrumentator import Instrumentator
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

resource = Resource.create({"service.name": "patient-service"})
otel_provider = TracerProvider(resource=resource)
otel_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint="http://jaeger:4317", insecure=True)))
trace.set_tracer_provider(otel_provider)


@asynccontextmanager
async def lifespan(app):
    await kafka_producer.start_producer()
    await kafka_consumer.start_consumer()
    asyncio.create_task(kafka_consumer.consume_events())
    yield
    await kafka_producer.stop_producer()
    await kafka_consumer.stop_consumer()


app = FastAPI(title="Patient Service", description="Patient records. Staff register and manage patients; deletes are soft deletes (is_deleted).", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # learners run their frontends on arbitrary origins; auth uses bearer tokens, not cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
FastAPIInstrumentor.instrument_app(app, excluded_urls="/metrics")
Instrumentator().instrument(app).expose(app, include_in_schema=False)

app.include_router(patient.router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "patient-service"}
