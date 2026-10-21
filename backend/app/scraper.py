import random

PLATFORMS = ["Amazon", "Flipkart", "1mg", "Blinkit", "BigBasket", "Nykaa"]


def get_mock_deals(query: str, limit: int = 6):
    offers = []
    for i in range(limit):
        platform = random.choice(PLATFORMS)
        price = random.randint(90, 2200)
        mrp = int(price * random.uniform(1.15, 1.85))
        discount = int(((mrp - price) / mrp) * 100)
        offers.append(
            {
                "platform": platform,
                "title": f"{query.capitalize()} deal {i + 1} — Special Offer",
                "price": f"₹{price}",
                "mrp": f"₹{mrp}",
                "discount": f"{discount}% OFF",
                "category": "General",
                "votes": random.randint(20, 500),
                "link": "https://example.com/deal",
            }
        )
    return offers
