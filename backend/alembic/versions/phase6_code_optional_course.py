"""phase6 code optional course and language c

Revision ID: phase6_001
Revises: phase5_001
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "phase6_001"
down_revision: Union[str, None] = "phase5_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "code_submission",
        "course_id",
        existing_type=sa.BigInteger(),
        nullable=True,
    )
    op.execute(
        "ALTER TABLE code_submission MODIFY COLUMN language "
        "ENUM('c','cpp','python','java') NOT NULL"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE code_submission MODIFY COLUMN language "
        "ENUM('python','java','cpp') NOT NULL"
    )
    op.alter_column(
        "code_submission",
        "course_id",
        existing_type=sa.BigInteger(),
        nullable=False,
    )
