"""Add course approval columns (phase3). Safe to run multiple times."""
import os
import sys

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

from sqlalchemy import inspect, text

from app.core.database import engine


def _has_column(table: str, column: str) -> bool:
    insp = inspect(engine)
    return column in {c["name"] for c in insp.get_columns(table)}


def migrate() -> None:
    with engine.begin() as conn:
        if not _has_column("course", "create_approval"):
            conn.execute(
                text(
                    "ALTER TABLE course ADD COLUMN create_approval "
                    "ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'approved'"
                )
            )
            print("Added column: create_approval")

        if not _has_column("course", "publish_approval"):
            conn.execute(
                text(
                    "ALTER TABLE course ADD COLUMN publish_approval "
                    "ENUM('none', 'pending', 'approved', 'rejected') NOT NULL DEFAULT 'none'"
                )
            )
            print("Added column: publish_approval")

        if not _has_column("course", "published_at"):
            conn.execute(text("ALTER TABLE course ADD COLUMN published_at DATETIME NULL"))
            print("Added column: published_at")

        conn.execute(
            text(
                "UPDATE course SET published_at = updated_at "
                "WHERE status = 'published' AND published_at IS NULL"
            )
        )
        conn.execute(
            text(
                "UPDATE course SET create_approval = 'approved', publish_approval = 'approved' "
                "WHERE status = 'published' AND create_approval = 'approved'"
            )
        )

    print("Course approval migration completed.")


if __name__ == "__main__":
    migrate()
