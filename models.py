from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base


class DealStatus(str, enum.Enum):
    pending = "pending"
    live = "live"
    expired = "expired"
    rejected = "rejected"


class ElectronicsCategory(str, enum.Enum):
    mobile = "mobile"
    laptop = "laptop"
    audio = "audio"
    tv = "tv"
    appliance = "appliance"
    camera = "camera"
    wearable = "wearable"
    accessory = "accessory"
    other = "other"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(40), unique=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    deals: Mapped[list[Deal]] = relationship(back_populates="submitter")


class Store(Base):
    """Merchants: Amazon.in, Flipkart, Croma, etc. Phase 1 is India only."""

    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True)       # "amazon-in"
    name: Mapped[str] = mapped_column(String(100))
    domain: Mapped[str] = mapped_column(String(100), unique=True)    # "amazon.in"
    affiliate_network: Mapped[str | None] = mapped_column(String(30))  # "amazon_associates" | "cuelinks" | None


class Deal(Base):
    __tablename__ = "deals"
    __table_args__ = (
        CheckConstraint("price > 0", name="ck_deal_price_positive"),
        Index("ix_deals_status_created", "status", "created_at"),
        Index("ix_deals_category", "category"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)

    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"))
    submitter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Raw merchant URL. The /go/{deal_id} redirect builds the affiliate link from this.
    product_url: Mapped[str] = mapped_column(Text)

    # Pricing (INR only in phase 1)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    mrp: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    coupon_code: Mapped[str | None] = mapped_column(String(50))
    bank_offer: Mapped[str | None] = mapped_column(String(255))      # "10% off with HDFC cards"
    emi_available: Mapped[bool] = mapped_column(default=False)

    # Electronics fields
    category: Mapped[ElectronicsCategory] = mapped_column(
        Enum(ElectronicsCategory, name="electronics_category"), default=ElectronicsCategory.other
    )
    brand: Mapped[str | None] = mapped_column(String(80))
    model_number: Mapped[str | None] = mapped_column(String(120))
    warranty_months: Mapped[int | None] = mapped_column(Integer)
    specs: Mapped[dict | None] = mapped_column(JSONB)                # {"ram":"8GB","storage":"256GB"}

    status: Mapped[DealStatus] = mapped_column(
        Enum(DealStatus, name="deal_status"), default=DealStatus.live
    )
    score: Mapped[int] = mapped_column(Integer, default=0)           # denormalised vote sum
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    store: Mapped[Store] = relationship()
    submitter: Mapped[User] = relationship(back_populates="deals")
    votes: Mapped[list[Vote]] = relationship(back_populates="deal", cascade="all, delete-orphan")
    clicks: Mapped[list[Click]] = relationship(back_populates="deal", cascade="all, delete-orphan")


class Vote(Base):
    __tablename__ = "votes"
    __table_args__ = (
        UniqueConstraint("user_id", "deal_id", name="uq_vote_user_deal"),
        CheckConstraint("value IN (-1, 1)", name="ck_vote_value"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    deal_id: Mapped[int] = mapped_column(ForeignKey("deals.id", ondelete="CASCADE"))
    value: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    deal: Mapped[Deal] = relationship(back_populates="votes")


class Click(Base):
    """One row per /go/{deal_id} redirect."""

    __tablename__ = "clicks"
    __table_args__ = (Index("ix_clicks_deal_created", "deal_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    deal_id: Mapped[int] = mapped_column(ForeignKey("deals.id", ondelete="CASCADE"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    ip_hash: Mapped[str | None] = mapped_column(String(64))          # hashed, never store raw IP
    user_agent: Mapped[str | None] = mapped_column(String(300))
    referrer: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    deal: Mapped[Deal] = relationship(back_populates="clicks")
