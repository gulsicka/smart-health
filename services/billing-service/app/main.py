import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import invoice
from app import kafka_consumer
from app.database import Base, engine
from prometheus_fastapi_instrumentator import Instrumentator
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

resource = Resource.create({"service.name": "billing-service"})
otel_provider = TracerProvider(resource=resource)
otel_provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://jaeger:4317", insecure=True))
)
trace.set_tracer_provider(otel_provider)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    await kafka_consumer.start_consumer()
    asyncio.create_task(kafka_consumer.consume_events())
    yield
    await kafka_consumer.stop_consumer()


app = FastAPI(title="Billing Service", lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app, excluded_urls="/metrics")
Instrumentator().instrument(app).expose(app)

app.include_router(invoice.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "billing-service"}
