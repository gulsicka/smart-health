from fastapi import FastAPI
from contextlib import asynccontextmanager
from app import kafka_producer
from app.routers import patient
from prometheus_fastapi_instrumentator import Instrumentator
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

resource = Resource.create({"service.name": "patient-service"})
provider = TracerProvider(resource=resource)
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint="http://jaeger:4317", insecure=True)))
trace.set_tracer_provider(provider)

@asynccontextmanager
async def lifespan(app):
    await kafka_producer.start_producer()
    yield
    await kafka_producer.stop_producer()

app = FastAPI(lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app)
Instrumentator().instrument(app).expose(app)

app.include_router(patient.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "patient-service"}
