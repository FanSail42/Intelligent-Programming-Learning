"""phase8 pptx material type and warehouse

Revision ID: phase8_001
Revises: phase7_001
"""
from typing import Sequence, Union

from alembic import op

revision: str = "phase8_001"
down_revision: Union[str, None] = "phase7_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE course_material MODIFY COLUMN type "
        "ENUM('pdf','txt','md','pptx') NOT NULL"
    )
    op.execute(
        "ALTER TABLE material_warehouse MODIFY COLUMN material_type "
        "ENUM('pdf','txt','md','pptx') NOT NULL"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE course_material SET type='pdf' WHERE type='pptx'"
    )
    op.execute(
        "DELETE FROM material_warehouse WHERE material_type='pptx'"
    )
    op.execute(
        "ALTER TABLE course_material MODIFY COLUMN type "
        "ENUM('pdf','txt','md') NOT NULL"
    )
    op.execute(
        "ALTER TABLE material_warehouse MODIFY COLUMN material_type "
        "ENUM('pdf','txt','md') NOT NULL"
    )
