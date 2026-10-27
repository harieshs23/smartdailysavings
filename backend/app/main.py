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

from app.db import SessionLocal, get_db, Base
from app.models import Deal, Waitlist
from sqlalchemy import select, text
from app.scraper import get_mock_deals

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
    pass


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
        db = SessionLocal()
        try:
            try:
                rows = db.execute(
                    select(Deal).where(Deal.title.ilike(f"%{q}%")).order_by(Deal.votes.desc()).limit(12)
                ).scalars().all()
                deals = [
                    {
                        "platform": d.platform,
                        "title": d.title,
                        "price": d.price,
                        "mrp": d.mrp,
                        "discount": d.discount,
                        "category": d.category,
                        "votes": d.votes,
                        "link": d.link,
                    }
                    for d in rows
                ]
            except Exception:
                deals = []

            if len(deals) < 6:
                deals.extend(get_mock_deals(q, 6 - len(deals)))
            return {"query": q, "results": deals, "count": len(deals)}
        finally:
            db.close()


@app.post("/waitlist")
def join_waitlist(payload: WaitlistRequest):
    db = SessionLocal()
    try:
        existing = db.execute(select(Waitlist).where(Waitlist.email == payload.email)).scalar_one_or_none()
        if existing is None:
            new_waitlist = Waitlist(email=payload.email, notification_timestamp=datetime.utcnow())
            db.add(new_waitlist)
            db.commit()
        return {"status": "success", "message": "Successfully joined the waitlist!"}
    finally:
        db.close()


@app.get("/waitlist")
def list_waitlist():
    db = SessionLocal()
    try:
        rows = db.execute(select(Waitlist.email, Waitlist.created_at).order_by(Waitlist.created_at.desc()).limit(10)).all()
        return {"results": [{"email": row.email, "created_at": row.created_at.isoformat()} for row in rows]}
    finally:
        db.close()
