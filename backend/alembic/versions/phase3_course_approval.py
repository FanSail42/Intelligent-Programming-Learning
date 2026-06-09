"""phase3 course approval

Revision ID: phase3_001
Revises: phase2_001
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "phase3_001"
down_revision: Union[str, None] = "phase2_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "course",
        sa.Column(
            "create_approval",
            sa.Enum("pending", "approved", "rejected", name="coursecreateapproval"),
            nullable=False,
            server_default="approved",
        ),
    )
    op.add_column(
        "course",
        sa.Column(
            "publish_approval",
            sa.Enum("none", "pending", "approved", "rejected", name="coursepublishapproval"),
            nullable=False,
            server_default="none",
        ),
    )
    op.add_column("course", sa.Column("published_at", sa.DateTime(), nullable=True))

    op.execute(
        "UPDATE course SET published_at = updated_at "
        "WHERE status = 'published' AND published_at IS NULL"
    )


def downgrade() -> None:
    op.drop_column("course", "published_at")
    op.drop_column("course", "publish_approval")
    op.drop_column("course", "create_approval")
