from sqlalchemy import inspect, text

from app.core.database import engine

_COURSE_APPROVAL_COLUMNS = (
    (
        "create_approval",
        "ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'approved'",
    ),
    (
        "publish_approval",
        "ENUM('none', 'pending', 'approved', 'rejected') NOT NULL DEFAULT 'none'",
    ),
    ("published_at", "DATETIME NULL"),
)


def ensure_course_schema() -> None:
    """Add course approval columns when the DB schema lags behind the models."""
    insp = inspect(engine)
    existing = {c["name"] for c in insp.get_columns("course")}

    with engine.begin() as conn:
        for name, ddl in _COURSE_APPROVAL_COLUMNS:
            if name in existing:
                continue
            conn.execute(text(f"ALTER TABLE course ADD COLUMN {name} {ddl}"))

        conn.execute(
            text(
                "UPDATE course SET published_at = updated_at "
                "WHERE status = 'published' AND published_at IS NULL"
            )
        )


def ensure_warehouse_schema() -> None:
    """Add material warehouse table and course_material columns when schema lags."""
    insp = inspect(engine)
    tables = insp.get_table_names()

    with engine.begin() as conn:
        if "material_warehouse" not in tables:
            conn.execute(
                text(
                    """
                    CREATE TABLE material_warehouse (
                        id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(64) NOT NULL,
                        description TEXT NULL,
                        warehouse_kind ENUM('file_type','course') NOT NULL DEFAULT 'file_type',
                        course_subject ENUM('python','java','cpp') NULL,
                        material_type ENUM('pdf','txt','md') NOT NULL,
                        icon VARCHAR(32) NOT NULL DEFAULT '📦',
                        color VARCHAR(16) NOT NULL DEFAULT '#409eff',
                        sort_order INT NOT NULL DEFAULT 0,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        deleted INT NOT NULL DEFAULT 0,
                        INDEX ix_material_warehouse_material_type (material_type),
                        INDEX ix_material_warehouse_kind (warehouse_kind)
                    )
                    """
                )
            )

        if "course_material" in tables:
            mat_cols = {c["name"] for c in insp.get_columns("course_material")}
            if "warehouse_id" not in mat_cols:
                conn.execute(
                    text("ALTER TABLE course_material ADD COLUMN warehouse_id BIGINT NULL")
                )
                conn.execute(
                    text(
                        "CREATE INDEX ix_course_material_warehouse_id "
                        "ON course_material (warehouse_id)"
                    )
                )
            if "uploaded_by" not in mat_cols:
                conn.execute(
                    text("ALTER TABLE course_material ADD COLUMN uploaded_by BIGINT NULL")
                )
                conn.execute(
                    text(
                        "CREATE INDEX ix_course_material_uploaded_by "
                        "ON course_material (uploaded_by)"
                    )
                )

        if "material_warehouse" in insp.get_table_names():
            wh_cols = {c["name"] for c in insp.get_columns("material_warehouse")}
            if "warehouse_kind" not in wh_cols:
                conn.execute(
                    text(
                        "ALTER TABLE material_warehouse "
                        "ADD COLUMN warehouse_kind ENUM('file_type','course') "
                        "NOT NULL DEFAULT 'file_type'"
                    )
                )
            if "course_subject" not in wh_cols:
                conn.execute(
                    text(
                        "ALTER TABLE material_warehouse "
                        "ADD COLUMN course_subject ENUM('python','java','cpp') NULL"
                    )
                )
