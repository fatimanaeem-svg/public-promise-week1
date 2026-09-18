import os
import sqlite3
import uuid
from datetime import datetime, timezone

from . import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS submissions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    answer TEXT NOT NULL,
    device_token TEXT NOT NULL,
    ip TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_submissions_device_token ON submissions(device_token);
"""


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _connect()
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()


def has_submitted(device_token: str) -> bool:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT 1 FROM submissions WHERE device_token = ? LIMIT 1", (device_token,)
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def insert_submission(name: str, answer: str, device_token: str, ip: str) -> dict:
    submission = {
        "id": str(uuid.uuid4()),
        "name": name,
        "answer": answer,
        "device_token": device_token,
        "ip": ip,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO submissions (id, name, answer, device_token, ip, created_at) "
            "VALUES (:id, :name, :answer, :device_token, :ip, :created_at)",
            submission,
        )
        conn.commit()
    finally:
        conn.close()
    return submission


def get_all_submissions(order: str = "asc") -> list[dict]:
    direction = "ASC" if order == "asc" else "DESC"
    conn = _connect()
    try:
        rows = conn.execute(
            f"SELECT id, name, answer, created_at FROM submissions ORDER BY created_at {direction}"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_recent_submissions(limit: int = 20) -> list[dict]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT id, name, answer, created_at FROM submissions ORDER BY created_at ASC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
