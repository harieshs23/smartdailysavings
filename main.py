from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from scraper import fetch_deals

app = FastAPI(title="Smart Daily Savings API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to Smart Daily Savings API", "version": "1.0.0"}

@app.get("/deals")
async def get_deals(q: str = Query(..., description="Search query for deals")):
    """
    Fetch deals from various platforms based on the search query.
    """
    deals = fetch_deals(q)
    
    return {
        "query": q,
        "results": deals,
        "count": len(deals)
    }

@app.post("/waitlist")
async def join_waitlist(data: dict):
    """
    Endpoint to handle waitlist registrations.
    """
    email = data.get("email")
    # Placeholder: In a real app, save this to a database
    print(f"New waitlist registration: {email}")
    return {"status": "success", "message": "Successfully joined the waitlist!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
