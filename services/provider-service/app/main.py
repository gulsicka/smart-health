import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app import kafka_producer, kafka_consumer
from app.routers import department, clinic, provider, availability
from prometheus_fastapi_instrumentator import Instrumentator
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

resource = Resource.create({"service.name": "provider-service"})
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


app = FastAPI(lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app, excluded_urls="/metrics")
Instrumentator().instrument(app).expose(app)

app.include_router(department.router)
app.include_router(clinic.router)
app.include_router(provider.router)
app.include_router(availability.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "provider-service"}
