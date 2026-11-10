"""add email_verification table

Revision ID: 001_add_email_verification
Revises: 877fb6d9d9bd
Create Date: 2026-11-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_add_email_verification'
down_revision: Union[str, Sequence[str], None] = '877fb6d9d9bd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create email_verification table."""
    op.execute(
        """
        CREATE SCHEMA IF NOT EXISTS neon_auth;
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS neon_auth.email_verification (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            token VARCHAR(255) UNIQUE NOT NULL,
            "userId" UUID NOT NULL REFERENCES neon_auth."user"(id) ON DELETE CASCADE,
            email VARCHAR(255) NOT NULL,
            "expiresAt" TIMESTAMPTZ NOT NULL,
            "createdAt" TIMESTAMPTZ DEFAULT NOW(),
            "updatedAt" TIMESTAMPTZ DEFAULT NOW()
        );
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_email_verification_token
        ON neon_auth.email_verification (token);
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_email_verification_user
        ON neon_auth.email_verification ("userId");
        """
    )


def downgrade() -> None:
    """Drop email_verification table."""
    op.execute("DROP TABLE IF EXISTS neon_auth.email_verification;")
