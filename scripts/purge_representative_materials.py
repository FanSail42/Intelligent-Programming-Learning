"""
Purge course materials and Chroma vectors, keeping only representative files
for the three track courses (C++ DSA / Python data analysis / Java OOP).

Usage:
  python scripts/purge_representative_materials.py
  python scripts/purge_representative_materials.py --dry-run
  python scripts/purge_representative_materials.py --reprocess
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import get_redis
from app.models.course import Course
from app.models.material import CourseMaterial, MaterialChunk, MaterialStatus
from app.services.material_dispatch import dispatch_material_processing
from app.services.material_upload import remove_upload_file
from app.services.vector_store import get_vector_store

TRACK_COURSE_NAMES = (
    "C++ 数据结构与算法",
    "Python 数据分析",
    "Java 面向对象编程",
)

REPRESENTATIVE_DIRS: dict[str, list[Path]] = {
    "C++ 数据结构与算法": [
        ROOT / "root_data" / "课程资料" / "C++_竞赛算法",
        ROOT / "root_data" / "课程资料" / "_联调演示" / "dashboard_demo" / "cpp",
    ],
    "Python 数据分析": [
        ROOT / "root_data" / "课程资料" / "Python_数据分析",
        ROOT / "root_data" / "课程资料" / "_联调演示" / "dashboard_demo" / "python",
    ],
    "Java 面向对象编程": [
        ROOT / "root_data" / "课程资料" / "Java_面向对象编程",
        ROOT / "root_data" / "课程资料" / "_联调演示" / "dashboard_demo" / "java",
    ],
}


def _collect_keep_names() -> dict[str, set[str]]:
    keep: dict[str, set[str]] = {name: set() for name in TRACK_COURSE_NAMES}
    for course_name, dirs in REPRESENTATIVE_DIRS.items():
        for directory in dirs:
            if not directory.is_dir():
                continue
            for path in directory.iterdir():
                if path.is_file() and path.name != "README.md":
                    keep[course_name].add(path.name)
    return keep


def _resolve_track_courses(db: Session) -> dict[str, Course]:
    courses: dict[str, Course] = {}
    for name in TRACK_COURSE_NAMES:
        row = (
            db.query(Course)
            .filter(Course.name == name, Course.deleted == 0)
            .order_by(Course.id.asc())
            .first()
        )
        if row:
            courses[name] = row
    return courses


def purge_materials(*, dry_run: bool = False, reprocess: bool = False) -> dict:
    keep_names = _collect_keep_names()
    db = SessionLocal()
    store = get_vector_store()
    redis = get_redis()

    removed_materials = 0
    kept_materials = 0
    chroma_purged = 0
    reprocess_ids: list[int] = []

    try:
        track_courses = _resolve_track_courses(db)
        track_ids = {c.id for c in track_courses.values()}

        all_materials = (
            db.query(CourseMaterial)
            .filter(CourseMaterial.deleted == 0)
            .order_by(CourseMaterial.id.asc())
            .all()
        )

        course_name_by_id = {c.id: name for name, c in track_courses.items()}

        for material in all_materials:
            course_name = course_name_by_id.get(material.course_id)
            should_keep = (
                course_name is not None
                and material.original_name in keep_names.get(course_name, set())
            )

            if should_keep:
                kept_materials += 1
                if reprocess and material.status != MaterialStatus.ready:
                    reprocess_ids.append(material.id)
                continue

            removed_materials += 1
            if dry_run:
                print(
                    f"[dry-run] remove material id={material.id} "
                    f"course_id={material.course_id} name={material.original_name}"
                )
                continue

            material.deleted = 1
            db.query(MaterialChunk).filter(
                MaterialChunk.material_id == material.id
            ).update({"deleted": 1})
            try:
                store.delete_by_material(material.id)
                chroma_purged += 1
            except Exception as exc:
                print(f"warn: chroma delete material_id={material.id}: {exc}")
            redis.delete(f"material:status:{material.id}")

            file_path = material.file_path
            still_used = (
                db.query(CourseMaterial)
                .filter(
                    CourseMaterial.file_path == file_path,
                    CourseMaterial.deleted == 0,
                    CourseMaterial.id != material.id,
                )
                .count()
            )
            if still_used == 0:
                remove_upload_file(file_path)

        if not dry_run:
            db.commit()

        if reprocess and not dry_run:
            for material_id in reprocess_ids:
                dispatch_material_processing(material_id)

        report = {
            "track_courses": {name: c.id for name, c in track_courses.items()},
            "keep_names": {k: sorted(v) for k, v in keep_names.items()},
            "kept_materials": kept_materials,
            "removed_materials": removed_materials,
            "chroma_purged": chroma_purged,
            "reprocess_queued": len(reprocess_ids),
            "dry_run": dry_run,
        }
        return report
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Purge non-representative course materials")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing")
    parser.add_argument(
        "--reprocess",
        action="store_true",
        help="Re-queue processing for kept materials not in READY state",
    )
    args = parser.parse_args()

    report = purge_materials(dry_run=args.dry_run, reprocess=args.reprocess)
    print("=== Purge representative materials ===")
    for key, value in report.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
