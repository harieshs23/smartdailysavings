"""add notification_timestamp to waitlist

Revision ID: e95e4baded10
Revises: 877fb6d9d9bd
Create Date: 2026-10-27 19:55:57.150145

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e95e4baded10'
down_revision: Union[str, Sequence[str], None] = '877fb6d9d9bd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
