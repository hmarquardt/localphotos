"""Make user hashed_password nullable for OAuth

Revision ID: 1dcbfaad8956
Revises: 0564f93fe220
Create Date: 2025-03-31 14:20:47.262833

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel # Import sqlmodel for type usage if needed
import geoalchemy2 # Import geoalchemy2 for type usage if needed

# revision identifiers, used by Alembic.
revision: str = '1dcbfaad8956'
down_revision: Union[str, None] = '0564f93fe220'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Make user.hashed_password nullable."""
    op.alter_column('user', 'hashed_password',
               existing_type=sa.VARCHAR(), # Use VARCHAR or appropriate type from your DB
               nullable=True)


def downgrade() -> None:
    """Make user.hashed_password non-nullable."""
    # Note: This might fail if there are NULL values in the column.
    # Consider adding logic to handle NULLs before making non-nullable if necessary.
    op.alter_column('user', 'hashed_password',
               existing_type=sa.VARCHAR(), # Use VARCHAR or appropriate type from your DB
               nullable=False)
