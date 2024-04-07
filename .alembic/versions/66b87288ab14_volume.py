"""volume

Revision ID: 66b87288ab14
Revises: 
Create Date: 2024-04-07 15:40:53.929358

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from data import db, Product



# revision identifiers, used by Alembic.
revision: str = '66b87288ab14'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # add volume column to product table
    op.add_column('product', sa.Column('volume', sa.Float(), nullable=True))


def downgrade() -> None:
    # drop volume column from product table
    op.drop_column('product', 'volume')
