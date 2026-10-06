import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import user, role
from app import kafka_producer, kafka_consumer
from app.seed import seed_admin
from prometheus_fastapi_instrumentator import Instrumentator
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

resource = Resource.create({"service.name": "auth-service"})
otel_provider = TracerProvider(resource=resource)
otel_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint="http://jaeger:4317", insecure=True)))
trace.set_tracer_provider(otel_provider)


@asynccontextmanager
async def lifespan(app):
    # ensures a fresh deployment always has roles and a default admin
    # account (admin@smarthealth.com / the SYSTEM_PASSWORD setting) to log
    # in with, without requiring a manual seed step. No-op if already seeded.
    try:
        seed_admin()
    except Exception as e:
        print(f"Admin seed skipped: {e}")
    await kafka_producer.start_producer()
    await kafka_consumer.start_consumer()
    asyncio.create_task(kafka_consumer.consume_events())
    yield
    await kafka_producer.stop_producer()
    await kafka_consumer.stop_consumer()


app = FastAPI(title="Auth Service", description="Logins, users and roles. Log in here to get the bearer token every other service expects.", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # learners run their frontends on arbitrary origins; auth uses bearer tokens, not cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
FastAPIInstrumentor.instrument_app(app, excluded_urls="/metrics")
Instrumentator().instrument(app).expose(app, include_in_schema=False)

app.include_router(user.router)
app.include_router(role.router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "auth-service"}
