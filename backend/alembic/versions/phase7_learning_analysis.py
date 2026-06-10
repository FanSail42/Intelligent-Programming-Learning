"""phase7 learning analysis

Revision ID: phase7_001
Revises: phase6_001
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "phase7_001"
down_revision: Union[str, None] = "phase6_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "knowledge_point",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("course_id", sa.BigInteger(), nullable=False),
        sa.Column("parent_id", sa.BigInteger(), nullable=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_point_course_id", "knowledge_point", ["course_id"])

    op.create_table(
        "learning_event",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("course_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "event_type",
            sa.Enum(
                "code_submit",
                "code_analysis_error",
                "chat_message",
                "chat_no_context",
                "material_view",
                name="learningeventtype",
            ),
            nullable=False,
        ),
        sa.Column("kp_id", sa.BigInteger(), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_learning_event_user_id", "learning_event", ["user_id"])
    op.create_index("ix_learning_event_event_type", "learning_event", ["event_type"])

    op.create_table(
        "wrong_question_book",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("course_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "source_type",
            sa.Enum("code_submission", "chat_message", name="wrongquestionsourcetype"),
            nullable=False,
        ),
        sa.Column("ref_id", sa.BigInteger(), nullable=False),
        sa.Column("kp_id", sa.BigInteger(), nullable=True),
        sa.Column("mastered", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_wrong_question_book_user_id", "wrong_question_book", ["user_id"])

    op.create_table(
        "user_kp_mastery",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("kp_id", sa.BigInteger(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_kp_mastery_user_id", "user_kp_mastery", ["user_id"])
    op.create_index("ix_user_kp_mastery_kp_id", "user_kp_mastery", ["kp_id"])


def downgrade() -> None:
    op.drop_index("ix_user_kp_mastery_kp_id", table_name="user_kp_mastery")
    op.drop_index("ix_user_kp_mastery_user_id", table_name="user_kp_mastery")
    op.drop_table("user_kp_mastery")
    op.drop_index("ix_wrong_question_book_user_id", table_name="wrong_question_book")
    op.drop_table("wrong_question_book")
    op.drop_index("ix_learning_event_event_type", table_name="learning_event")
    op.drop_index("ix_learning_event_user_id", table_name="learning_event")
    op.drop_table("learning_event")
    op.drop_index("ix_knowledge_point_course_id", table_name="knowledge_point")
    op.drop_table("knowledge_point")
