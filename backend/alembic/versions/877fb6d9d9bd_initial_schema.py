"""initial_schema

Revision ID: 877fb6d9d9bd
Revises: 
Create Date: 2026-10-26 15:55:56.123266

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "877fb6d9d9bd"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the initial schema for the DealPulse app."""
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
                CREATE TYPE user_role AS ENUM ('user', 'moderator', 'admin');
            END IF;
        END $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'deal_status') THEN
                CREATE TYPE deal_status AS ENUM ('new', 'popular', 'frontpage', 'expired', 'removed');
            END IF;
        END $$;
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            email VARCHAR(255) UNIQUE NOT NULL,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            avatar_url TEXT,
            role user_role DEFAULT 'user',
            reputation_score INT DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS stores (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name VARCHAR(100) UNIQUE NOT NULL,
            slug VARCHAR(100) UNIQUE NOT NULL,
            domain VARCHAR(255) NOT NULL,
            affiliate_network VARCHAR(50),
            affiliate_template_url TEXT,
            logo_url TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS categories (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name VARCHAR(50) UNIQUE NOT NULL,
            slug VARCHAR(50) UNIQUE NOT NULL,
            parent_id UUID REFERENCES categories(id) ON DELETE SET NULL
        );
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS deals (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            store_id UUID NOT NULL REFERENCES stores(id) ON DELETE RESTRICT,
            category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
            title VARCHAR(255) NOT NULL,
            slug VARCHAR(255) UNIQUE NOT NULL,
            description TEXT NOT NULL,
            original_price DECIMAL(10, 2),
            sale_price DECIMAL(10, 2) NOT NULL,
            coupon_code VARCHAR(50),
            direct_url TEXT NOT NULL,
            image_url TEXT,
            status deal_status DEFAULT 'new',
            score INT DEFAULT 0,
            views_count INT DEFAULT 0,
            clicks_count INT DEFAULT 0,
            is_free_shipping BOOLEAN DEFAULT FALSE,
            expires_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_deals_status_score
        ON deals (status, score DESC);
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_deals_store
        ON deals (store_id);
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_deals_category
        ON deals (category_id);
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS votes (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
            value SMALLINT NOT NULL CHECK (value IN (-1, 1)),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE (user_id, deal_id)
        );
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS comments (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            parent_id UUID REFERENCES comments(id) ON DELETE CASCADE,
            body TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_comments_deal
        ON comments (deal_id);
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS deal_alerts (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            keyword VARCHAR(100),
            store_id UUID REFERENCES stores(id) ON DELETE CASCADE,
            max_price DECIMAL(10, 2),
            min_score INT DEFAULT 5,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS deal_clicks (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
            user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            ip_address INET,
            user_agent TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    )


def downgrade() -> None:
    """Drop the initial schema."""
    op.execute("DROP TABLE IF EXISTS deal_clicks;")
    op.execute("DROP TABLE IF EXISTS deal_alerts;")
    op.execute("DROP TABLE IF EXISTS comments;")
    op.execute("DROP TABLE IF EXISTS votes;")
    op.execute("DROP INDEX IF EXISTS idx_deals_status_score;")
    op.execute("DROP INDEX IF EXISTS idx_deals_store;")
    op.execute("DROP INDEX IF EXISTS idx_deals_category;")
    op.execute("DROP TABLE IF EXISTS deals;")
    op.execute("DROP TABLE IF EXISTS categories;")
    op.execute("DROP TABLE IF EXISTS stores;")
    op.execute("DROP TABLE IF EXISTS users;")

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'deal_status') THEN
                DROP TYPE deal_status;
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
                DROP TYPE user_role;
            END IF;
        END $$;
        """
    )
