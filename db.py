import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


# App runtime: use Neon's POOLED connection string (host contains "-pooler").
# Alembic: use the DIRECT connection string (see ALEMBIC_DATABASE_URL in alembic/env.py).
DATABASE_URL = os.environ["DATABASE_URL"]

# psycopg v3 driver: postgresql+psycopg://user:pass@host/db?sslmode=require
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # Neon computes can suspend; drop dead connections
    pool_recycle=300,
    pool_size=5,
    max_overflow=5,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    """FastAPI dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
