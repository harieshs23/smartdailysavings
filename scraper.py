import requests
from bs4 import BeautifulSoup
import random
import time

# Use a real User-Agent to avoid being blocked immediately
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

def scrape_desidime(query):
    """
    Scrape deals from Desidime (a popular Indian deal community).
    """
    deals = []
    try:
        # Desidime search URL
        url = f"https://www.desidime.com/search?q={query}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Finding deal cards (this selector might need updates if the website changes)
            items = soup.select('.deal-container')
            
            for item in items[:10]: # Limit to 10 results
                try:
                    title_elem = item.select_one('.deal-title a')
                    price_elem = item.select_one('.deal-price')
                    
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        link = "https://www.desidime.com" + title_elem['href']
                        price = price_elem.get_text(strip=True) if price_elem else "Check Site"
                        
                        deals.append({
                            "platform": "Desidime",
                            "title": title,
                            "price": price,
                            "mrp": "", # Not always available on search page
                            "discount": "Hot Deal",
                            "category": "Deals",
                            "votes": random.randint(50, 200),
                            "link": link
                        })
                except Exception as e:
                    print(f"Error parsing item: {e}")
                    continue
    except Exception as e:
        print(f"Scraping error: {e}")
        
    return deals

def fetch_deals(query):
    """
    Combined deal fetcher. Tries real scraping and falls back to/mixes with mock data.
    """
    # 1. Try real scraping (Example: Desidime)
    real_deals = scrape_desidime(query)
    
    # 2. Generate some mock data for variety if real results are low
    platforms = ["Amazon", "Flipkart", "1mg", "Blinkit"]
    mock_deals = []
    
    if len(real_deals) < 5:
        for i in range(5 - len(real_deals)):
            platform = random.choice(platforms)
            price = random.randint(100, 2000)
            mrp = int(price * (1 + random.uniform(0.1, 0.5)))
            discount = int(((mrp - price) / mrp) * 100)
            
            mock_deals.append({
                "platform": platform,
                "title": f"[Mock] {query.capitalize()} {i+1} - Special Deal",
                "price": f"₹{price}",
                "mrp": f"₹{mrp}",
                "discount": f"{discount}% OFF",
                "category": "General",
                "votes": random.randint(10, 500)
            })
    
    return real_deals + mock_deals
