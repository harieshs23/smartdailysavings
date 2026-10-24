import os

from celery import Celery
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from pydantic import BaseModel, EmailStr

from app.database import get_connection, init_db
from app.scraper import get_mock_deals

init_db()

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_BACKEND_URL = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery(
    "smartdailysavings",
    broker=CELERY_BROKER_URL,
    backend=CELERY_BACKEND_URL,
)


@celery_app.task
def fetch_deals_task(query: str, limit: int = 6):
    return get_mock_deals(query, limit)


resource = Resource.create({"service.name": "smartdailysavings"})
provider = TracerProvider(resource=resource)
try:
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
except Exception:
    provider.add_span_processor(BatchSpanProcessor())

trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

app = FastAPI(title="Smart Daily Savings API", version="1.0.0")
FastAPIInstrumentor.instrument_app(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class WaitlistRequest(BaseModel):
    email: EmailStr


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/")
def root():
    with tracer.start_as_current_span("root"):
        return {"message": "Welcome to Smart Daily Savings API", "version": "1.0.0"}


@app.get("/health")
def health():
    with tracer.start_as_current_span("health"):
        return {"status": "ok"}


@app.get("/deals")
def get_deals(q: str = Query(..., min_length=1)):
    with tracer.start_as_current_span("get_deals") as span:
        span.set_attribute("query", q)
        try:
            task = fetch_deals_task.delay(q, 6)
            return {
                "query": q,
                "results": get_mock_deals(q, 6),
                "count": 6,
                "task_id": task.id,
                "status": "queued",
            }
        except Exception:
            conn = get_connection()
            rows = conn.execute(
                "SELECT platform, title, price, mrp, discount, category, votes, link FROM deals WHERE title LIKE ? ORDER BY votes DESC LIMIT 12",
                (f"%{q}%",),
            ).fetchall()
            conn.close()

            deals = [dict(row) for row in rows]
            if len(deals) < 6:
                deals.extend(get_mock_deals(q, 6 - len(deals)))

            return {"query": q, "results": deals, "count": len(deals)}


@app.post("/waitlist")
def join_waitlist(payload: WaitlistRequest):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO waitlist (email) VALUES (?)",
            (payload.email,),
        )
        conn.commit()
        return {"status": "success", "message": "Successfully joined the waitlist!"}
    finally:
        conn.close()


@app.get("/waitlist")
def list_waitlist():
    conn = get_connection()
    rows = conn.execute("SELECT email, created_at FROM waitlist ORDER BY created_at DESC LIMIT 10").fetchall()
    conn.close()
    return {"results": [dict(row) for row in rows]}
