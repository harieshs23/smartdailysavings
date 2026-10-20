import requests
from bs4 import BeautifulSoup
import random

def fetch_deals(query):
    """
    Combined deal fetcher for multiple platforms.
    Currently returns mock data but structured for real scraping.
    """
    platforms = ["Amazon", "Flipkart", "1mg", "BigBasket", "Blinkit"]
    
    # Simulate finding different results for different queries
    deals = []
    
    # In a real app, we would have specific scrapers for each platform
    # For now, let's generate some mock data based on the query
    
    for i in range(5):
        platform = random.choice(platforms)
        price = random.randint(100, 2000)
        mrp = int(price * (1 + random.uniform(0.1, 0.5)))
        discount = int(((mrp - price) / mrp) * 100)
        
        deals.append({
            "platform": platform,
            "title": f"{query.capitalize()} {i+1} - Special Deal",
            "price": f"₹{price}",
            "mrp": f"₹{mrp}",
            "discount": f"{discount}% OFF",
            "category": "General",
            "votes": random.randint(10, 500)
        })
        
    return deals
