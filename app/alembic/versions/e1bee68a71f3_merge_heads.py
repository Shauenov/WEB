"""merge heads

Revision ID: e1bee68a71f3
Revises: 76e60e2b5da8, ef660076447b
Create Date: 2025-09-25 03:46:11.418252

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'e1bee68a71f3'
down_revision: Union[str, None] = ('76e60e2b5da8', 'ef660076447b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
