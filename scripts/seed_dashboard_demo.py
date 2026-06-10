#!/usr/bin/env python3
"""Seed dashboard demo: 3 courses, 18 materials, 40+ wrong-book rows. Safe to re-run."""
import os
import sys

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(BACKEND_DIR)

from app.core.database import SessionLocal
from dashboard_demo_data import seed_dashboard_demo, write_manifest
from generate_dashboard_materials import generate_all


def main() -> None:
    print("Step 1/3: generate PDF materials ...")
    generate_all()

    print("Step 2/3: seed database ...")
    db = SessionLocal()
    try:
        report = seed_dashboard_demo(db)
    finally:
        db.close()

    print("Step 3/3: write manifest ...")
    write_manifest(report)

    print("Dashboard demo seed complete:")
    print(f"  courses={len(report['courses'])}")
    print(f"  wrong_code={report['totals']['wrong_code']}, wrong_chat={report['totals']['wrong_chat']}")
    print(f"  materials={report['totals']['materials']}, events={report['totals']['events']}")
    for c in report["courses"]:
        print(f"  - [{c['key']}] {c['name']} (id={c['id']})")


if __name__ == "__main__":
    main()
