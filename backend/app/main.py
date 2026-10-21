from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

from app.database import get_connection, init_db
from app.scraper import get_mock_deals

init_db()

app = FastAPI(title="Smart Daily Savings API", version="1.0.0")

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
    return {"message": "Welcome to Smart Daily Savings API", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/deals")
def get_deals(q: str = Query(..., min_length=1)):
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
