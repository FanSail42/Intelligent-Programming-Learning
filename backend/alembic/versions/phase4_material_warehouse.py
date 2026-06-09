"""phase4 material warehouse

Revision ID: phase4_001
Revises: phase3_001
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "phase4_001"
down_revision: Union[str, None] = "phase3_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "material_warehouse",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "material_type",
            sa.Enum("pdf", "txt", "md", name="materialtype"),
            nullable=False,
        ),
        sa.Column("icon", sa.String(length=32), nullable=False),
        sa.Column("color", sa.String(length=16), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_material_warehouse_material_type", "material_warehouse", ["material_type"])

    op.add_column("course_material", sa.Column("warehouse_id", sa.BigInteger(), nullable=True))
    op.add_column("course_material", sa.Column("uploaded_by", sa.BigInteger(), nullable=True))
    op.create_index("ix_course_material_warehouse_id", "course_material", ["warehouse_id"])
    op.create_index("ix_course_material_uploaded_by", "course_material", ["uploaded_by"])


def downgrade() -> None:
    op.drop_index("ix_course_material_uploaded_by", table_name="course_material")
    op.drop_index("ix_course_material_warehouse_id", table_name="course_material")
    op.drop_column("course_material", "uploaded_by")
    op.drop_column("course_material", "warehouse_id")
    op.drop_index("ix_material_warehouse_material_type", table_name="material_warehouse")
    op.drop_table("material_warehouse")
