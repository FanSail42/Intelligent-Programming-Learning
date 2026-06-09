"""Insert stu / tea / adm demo accounts (password: 123123)."""
import os
import sys

import bcrypt

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.user import User, UserRole, UserStatus

ACCOUNTS = [
    ("stu", UserRole.student),
    ("tea", UserRole.teacher),
    ("adm", UserRole.admin),
]
PASSWORD = "123123"


def seed_accounts() -> None:
    password_hash = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt()).decode()
    db = SessionLocal()
    try:
        created = []
        for username, role in ACCOUNTS:
            existing = db.query(User).filter(User.username == username).first()
            if existing:
                continue
            db.add(
                User(
                    username=username,
                    password_hash=password_hash,
                    role=role,
                    status=UserStatus.active,
                )
            )
            created.append(username)
        db.commit()
        if created:
            print(f"Created accounts: {', '.join(created)} (password: {PASSWORD})")
        else:
            print("Accounts stu/tea/adm already exist")
    finally:
        db.close()


if __name__ == "__main__":
    seed_accounts()
