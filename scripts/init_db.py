"""Create database and run migrations."""
import pymysql

conn = pymysql.connect(
    host="127.0.0.1",
    port=3307,
    user="root",
    password="lifan",
    charset="utf8mb4",
)
try:
    with conn.cursor() as cur:
        cur.execute(
            "CREATE DATABASE IF NOT EXISTS huibian "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
    conn.commit()
    print("Database huibian ready")
finally:
    conn.close()
