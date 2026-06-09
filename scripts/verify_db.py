import pymysql

conn = pymysql.connect(
    host="127.0.0.1",
    port=3307,
    user="root",
    password="lifan",
    database="huibian",
    charset="utf8mb4",
)
with conn.cursor() as cur:
    cur.execute("SHOW TABLES")
    print("Tables:", [r[0] for r in cur.fetchall()])
    cur.execute("SELECT COUNT(*) FROM `user`")
    print("user count:", cur.fetchone()[0])
    cur.execute("SELECT COUNT(*) FROM course")
    print("course count:", cur.fetchone()[0])
    cur.execute("SELECT id, username, role FROM `user`")
    print("users:", cur.fetchall())
    cur.execute("SELECT id, name, status, create_approval, publish_approval, published_at FROM course")
    print("courses:", cur.fetchall())
conn.close()
