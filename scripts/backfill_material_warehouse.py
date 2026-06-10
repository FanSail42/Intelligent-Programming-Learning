"""Backfill course_material.warehouse_id and reassign pptx to PPTX warehouse."""
import os
import sys

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from app.core.db_migrate import ensure_material_schema
from app.core.database import SessionLocal
from seed_warehouses import seed


def main() -> None:
    ensure_material_schema()
    seed()


if __name__ == "__main__":
    main()
