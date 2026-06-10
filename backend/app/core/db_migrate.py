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
                        material_type ENUM('pdf','txt','md','pptx') NOT NULL,
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
            mat_indexes = {idx["name"] for idx in insp.get_indexes("course_material")}
            if "ix_course_material_name_deleted" not in mat_indexes:
                conn.execute(
                    text(
                        "CREATE INDEX ix_course_material_name_deleted "
                        "ON course_material (original_name, deleted)"
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

        if "course_material" in insp.get_table_names() and engine.dialect.name == "mysql":
            type_col = next(
                (c for c in insp.get_columns("course_material") if c["name"] == "type"),
                None,
            )
            if type_col:
                col_type = str(type_col.get("type", ""))
                if "pptx" not in col_type:
                    conn.execute(
                        text(
                            "ALTER TABLE course_material MODIFY COLUMN type "
                            "ENUM('pdf','txt','md','pptx') NOT NULL"
                        )
                    )

        if "material_warehouse" in insp.get_table_names() and engine.dialect.name == "mysql":
            wh_type_col = next(
                (c for c in insp.get_columns("material_warehouse") if c["name"] == "material_type"),
                None,
            )
            if wh_type_col:
                wh_col_type = str(wh_type_col.get("type", ""))
                if "pptx" not in wh_col_type:
                    conn.execute(
                        text(
                            "ALTER TABLE material_warehouse MODIFY COLUMN material_type "
                            "ENUM('pdf','txt','md','pptx') NOT NULL"
                        )
                    )


def ensure_material_schema() -> None:
    """Extend course_material.type enum for pptx uploads."""
    ensure_warehouse_schema()


def ensure_code_schema() -> None:
    """Create code analysis tables when Alembic phase5 has not been applied."""
    insp = inspect(engine)
    tables = insp.get_table_names()

    with engine.begin() as conn:
        if "code_submission" not in tables:
            conn.execute(
                text(
                    """
                    CREATE TABLE code_submission (
                        id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        course_id BIGINT NULL,
                        assignment_id BIGINT NULL,
                        language ENUM('c','cpp','python','java') NOT NULL,
                        source_code TEXT NOT NULL,
                        version INT NOT NULL DEFAULT 1,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        deleted INT NOT NULL DEFAULT 0,
                        INDEX ix_code_submission_user_id (user_id),
                        INDEX ix_code_submission_course_id (course_id)
                    )
                    """
                )
            )
        elif "code_submission" in tables and engine.dialect.name == "mysql":
            cols = {c["name"] for c in insp.get_columns("code_submission")}
            if "course_id" in cols:
                course_col = next(c for c in insp.get_columns("code_submission") if c["name"] == "course_id")
                if not course_col.get("nullable"):
                    conn.execute(
                        text("ALTER TABLE code_submission MODIFY course_id BIGINT NULL")
                    )
            conn.execute(
                text(
                    "ALTER TABLE code_submission MODIFY COLUMN language "
                    "ENUM('c','cpp','python','java') NOT NULL"
                )
            )

        if "analysis_result" not in tables:
            conn.execute(
                text(
                    """
                    CREATE TABLE analysis_result (
                        id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        submission_id BIGINT NOT NULL,
                        status ENUM('pending','running','done','failed') NOT NULL,
                        result_json JSON NULL,
                        error_message VARCHAR(512) NULL,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        deleted INT NOT NULL DEFAULT 0,
                        UNIQUE INDEX ix_analysis_result_submission_id (submission_id)
                    )
                    """
                )
            )


def ensure_learning_schema() -> None:
    """Create M06 learning analysis tables when Alembic phase7 has not been applied."""
    insp = inspect(engine)
    tables = insp.get_table_names()

    with engine.begin() as conn:
        if "knowledge_point" not in tables:
            conn.execute(
                text(
                    """
                    CREATE TABLE knowledge_point (
                        id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        course_id BIGINT NOT NULL,
                        parent_id BIGINT NULL,
                        name VARCHAR(128) NOT NULL,
                        sort_order INT NOT NULL,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        deleted INT NOT NULL DEFAULT 0,
                        INDEX ix_knowledge_point_course_id (course_id)
                    )
                    """
                )
            )

        if "learning_event" not in tables:
            conn.execute(
                text(
                    """
                    CREATE TABLE learning_event (
                        id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        course_id BIGINT NULL,
                        event_type ENUM(
                            'code_submit','code_analysis_error','chat_message',
                            'chat_no_context','material_view'
                        ) NOT NULL,
                        kp_id BIGINT NULL,
                        payload_json JSON NULL,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        deleted INT NOT NULL DEFAULT 0,
                        INDEX ix_learning_event_user_id (user_id),
                        INDEX ix_learning_event_event_type (event_type)
                    )
                    """
                )
            )

        if "wrong_question_book" not in tables:
            conn.execute(
                text(
                    """
                    CREATE TABLE wrong_question_book (
                        id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        course_id BIGINT NULL,
                        source_type ENUM('code_submission','chat_message') NOT NULL,
                        ref_id BIGINT NOT NULL,
                        kp_id BIGINT NULL,
                        mastered TINYINT(1) NOT NULL DEFAULT 0,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        deleted INT NOT NULL DEFAULT 0,
                        INDEX ix_wrong_question_book_user_id (user_id)
                    )
                    """
                )
            )

        if "user_kp_mastery" not in tables:
            conn.execute(
                text(
                    """
                    CREATE TABLE user_kp_mastery (
                        id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        kp_id BIGINT NOT NULL,
                        score INT NOT NULL,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        deleted INT NOT NULL DEFAULT 0,
                        INDEX ix_user_kp_mastery_user_id (user_id),
                        INDEX ix_user_kp_mastery_kp_id (kp_id)
                    )
                    """
                )
            )
