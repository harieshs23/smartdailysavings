from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
from pydantic import BaseModel
from scraper import fetch_deals
from app.database import get_connection, init_db
from celery import Celery
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.exporter import OTLPSpanExporter

# OpenTelemetry setup
trace.set_tracer_provider(TracerProvider())
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))
tracer = trace.get_tracer(__name__)

# Celery + Redis orchestration setup
celery_app = Celery(
    "smartdailysavings",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)


@celery_app.task
def async_fetch_deals(query: str, limit: int = 6):
    """Background task to fetch deals."""
    return fetch_deals(query, limit)


app = FastAPI(title="Smart Daily Savings API")

# Initialize OpenTelemetry instrumentation
FastAPIInstrumentor.instrument_app(app)

# Initialize database on startup
init_db()

# Models for API validation and automatic docs
class Deal(BaseModel):
    platform: str
    title: str
    price: str
    mrp: str
    discount: str
    category: str
    votes: int
    link: Optional[str] = None

class DealsResponse(BaseModel):
    query: str
    results: List[Deal]
    count: int

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    # Ensure OTLP exporter connection
    pass

@app.get("/")
async def root():
    with tracer.start_as_current_span("root-endpoint") as span:
        span.set_attribute("endpoint", "/")
        return {"message": "Welcome to Smart Daily Savings API", "version": "1.0.0"}

@app.get("/deals", response_model=DealsResponse)
async def get_deals(q: str = Query(..., description="Search query for deals")):
    """
    Fetch deals from various platforms.
    Triggers async fetch via Celery/Redis orchestration with OpenTelemetry tracing.
    """
    with tracer.start_as_current_span("get-deals") as span:
        span.set_attribute("query", q)
        # Launch background task
        task = async_fetch_deals.delay(q=q, limit=6)
        return {
            "query": q,
            "task_id": task.id,
            "status": "processing",
            "message": "Deal fetch started asynchronously via Celery/Redis"
        }

@app.post("/waitlist")
async def join_waitlist(data: dict):
    """
    Endpoint to handle waitlist registrations.
    """
    email = data.get("email")
    # Use the database connection
    conn = get_connection()
    conn.execute(
        "INSERT INTO waitlist (email) VALUES (%s)",
        (email,)
    )
    conn.commit()
    print(f"New waitlist registration: {email}")
    return {"status": "success", "message": "Successfully joined the waitlist!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
