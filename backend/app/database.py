import os
import urllib.parse
from pathlib import Path

DB_PATH = Path(
    os.environ.get(
        "DATABASE_PATH",
        Path(__file__).resolve().parent.parent / "smartdailysavings.db",
    )
)
DATABASE_URL = os.environ.get("DATABASE_URL")


def _is_postgres_url(url: str | None) -> bool:
    if not url:
        return False
    parsed = urllib.parse.urlparse(url)
    return parsed.scheme in {"postgresql", "postgres", "postgresql+psycopg2"}


if _is_postgres_url(DATABASE_URL):
    import psycopg2

    _pg_conn = None

    def get_connection():
        global _pg_conn
        if _pg_conn is None or _pg_conn.closed:
            _pg_conn = psycopg2.connect(DATABASE_URL)
        return _pg_conn

    def init_db():
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS waitlist (
                    id SERIAL PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS deals (
                    id SERIAL PRIMARY KEY,
                    platform TEXT NOT NULL,
                    title TEXT NOT NULL,
                    price TEXT NOT NULL,
                    mrp TEXT,
                    discount TEXT,
                    category TEXT,
                    votes INTEGER DEFAULT 0,
                    link TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )
            cur.execute(
                """
                INSERT INTO deals (platform, title, price, mrp, discount, category, votes, link)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (
                    "BigBasket",
                    "Fortune Sunlite Refined Sunflower Oil 5L",
                    "₹549",
                    "₹620",
                    "54% OFF",
                    "Groceries",
                    143,
                    "https://www.bigbasket.com",
                ),
            )
        conn.commit()

else:
    import sqlite3

    def get_connection():
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        return conn

    def init_db():
        conn = get_connection()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS waitlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                title TEXT NOT NULL,
                price TEXT NOT NULL,
                mrp TEXT,
                discount TEXT,
                category TEXT,
                votes INTEGER DEFAULT 0,
                link TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO deals (platform, title, price, mrp, discount, category, votes, link)
            VALUES
                ('BigBasket', 'Fortune Sunlite Refined Sunflower Oil 5L', '₹549', '₹620', '54% OFF', 'Groceries', 143, 'https://www.bigbasket.com'),
                ('1mg', 'Metformin 500mg Generic — 60 tablets', '₹38', '₹245', 'GENERIC', 'Medicines', 89, 'https://www.1mg.com'),
                ('Flipkart', 'boAt Airdopes 141 True Wireless Earbuds', '₹899', '₹1,499', '40% OFF', 'Electronics', 312, 'https://www.flipkart.com'),
                ('Meesho', 'Cotton Solid Baseball Cap — Unisex', '₹129', '₹399', '67% OFF', 'Fashion', 204, 'https://www.meesho.com'),
                ('Amazon', 'Solimo Bamboo Cutlery Tray 4-Compartment Kitchen Organiser', '₹349', '₹539', '35% OFF', 'Home & Living', 76, 'https://www.amazon.in'),
                ('Nykaa', 'Zaveri Pearls Oxidised Silver Jhumka Earrings Set', '₹219', '₹399', '45% OFF', 'Ladies Accessories', 158, 'https://www.nykaa.com')
            """
        )
        conn.commit()
        conn.close()
