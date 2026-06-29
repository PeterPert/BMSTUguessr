from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from typing import Any

from . import paths
from .security import hash_password, verify_password

LOCK_AFTER_ATTEMPTS = 5
LOCK_SECONDS = 60
DEFAULT_ADMINS: list[tuple[str, str]] = [
    ("bmstu_admin1", "FrostBlue2026"),
    ("bmstu_admin2", "PortalSky2026"),
    ("bmstu_admin3", "VectorHall2026"),
    ("bmstu_admin4", "QuartzMap2026"),
    ("bmstu_admin5", "AuroraFloor2026"),
]


def connect() -> sqlite3.Connection:
    paths.ensure_dirs()
    conn = sqlite3.connect(paths.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def initialize_db() -> None:
    paths.ensure_dirs()
    with connect() as conn:
        _drop_legacy_tables(conn)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS floors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                place TEXT NOT NULL DEFAULT 'gz',
                floor_number INTEGER NOT NULL,
                map_path TEXT NOT NULL,
                meters_per_pixel REAL NOT NULL DEFAULT 0.1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(place, floor_number)
            );

            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                place TEXT NOT NULL DEFAULT 'gz',
                title TEXT,
                image_path TEXT NOT NULL,
                answer_x INTEGER NOT NULL,
                answer_y INTEGER NOT NULL,
                floor INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS game_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                score INTEGER NOT NULL,
                max_score INTEGER NOT NULL DEFAULT 30,
                played_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS game_session_rounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                round_number INTEGER NOT NULL,
                location_title TEXT,
                image_path TEXT,
                answer_x INTEGER NOT NULL,
                answer_y INTEGER NOT NULL,
                answer_floor INTEGER NOT NULL,
                guessed_x INTEGER NOT NULL,
                guessed_y INTEGER NOT NULL,
                guessed_floor INTEGER NOT NULL,
                distance_meters REAL NOT NULL,
                points INTEGER NOT NULL,
                FOREIGN KEY(session_id) REFERENCES game_sessions(id)
                    ON UPDATE CASCADE ON DELETE CASCADE
            );
            """)
        _insert_default_floors(conn)
        _seed_default_admins(conn)
        conn.commit()


def _drop_legacy_tables(conn: sqlite3.Connection) -> None:
    existing = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    legacy_tables = [
        name for name in ("game_rounds", "game_results", "users") if name in existing
    ]
    if not legacy_tables:
        return
    conn.execute("PRAGMA foreign_keys = OFF")
    for table_name in ("game_rounds", "game_results", "users"):
        if table_name in existing:
            conn.execute(f"DROP TABLE IF EXISTS {table_name}")
    conn.execute("PRAGMA foreign_keys = ON")


def _insert_default_floors(conn: sqlite3.Connection) -> None:
    defaults = [
        ("gz", 2, "data/maps/floor_2.png", 0.1),
        ("gz", 3, "data/maps/floor_3.png", 0.1),
    ]
    for place, floor_number, map_path, meters_per_pixel in defaults:
        if paths.resolve_path(map_path).exists():
            conn.execute(
                """
                INSERT OR IGNORE INTO floors(place, floor_number, map_path, meters_per_pixel)
                VALUES (?, ?, ?, ?)
                """,
                (place, floor_number, map_path, meters_per_pixel),
            )


def _seed_default_admins(conn: sqlite3.Connection) -> None:
    for username, password in DEFAULT_ADMINS:
        exists = conn.execute(
            "SELECT 1 FROM admins WHERE username = ?",
            (username,),
        ).fetchone()
        if exists:
            continue
        password_hash, password_salt = hash_password(password)
        conn.execute(
            """
            INSERT INTO admins(username, password_hash, password_salt)
            VALUES (?, ?, ?)
            """,
            (username, password_hash, password_salt),
        )


# ----- Администраторы -----


def authenticate_admin(
    username: str, password: str
) -> tuple[bool, str, dict[str, Any] | None]:
    username = username.strip()
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM admins WHERE username = ?",
            (username,),
        ).fetchone()
        if row is None:
            return False, "Неверный логин или пароль.", None

        admin = dict(row)
        locked_until = admin.get("locked_until")
        if locked_until:
            try:
                unlock_time = datetime.fromisoformat(locked_until)
            except ValueError:
                unlock_time = datetime.min
            if unlock_time > datetime.now():
                left = int((unlock_time - datetime.now()).total_seconds()) + 1
                return (
                    False,
                    f"Слишком много попыток. Повторите через {left} сек.",
                    None,
                )

        if not verify_password(
            password, admin["password_hash"], admin["password_salt"]
        ):
            failed = int(admin["failed_attempts"] or 0) + 1
            locked_value = None
            if failed >= LOCK_AFTER_ATTEMPTS:
                locked_value = (
                    datetime.now() + timedelta(seconds=LOCK_SECONDS)
                ).isoformat(timespec="seconds")
                failed = 0
            conn.execute(
                "UPDATE admins SET failed_attempts = ?, locked_until = ? WHERE id = ?",
                (failed, locked_value, admin["id"]),
            )
            conn.commit()
            return False, "Неверный логин или пароль.", None

        conn.execute(
            "UPDATE admins SET failed_attempts = 0, locked_until = NULL WHERE id = ?",
            (admin["id"],),
        )
        conn.commit()
        return (
            True,
            "Вход выполнен.",
            {"id": admin["id"], "username": admin["username"]},
        )


# ----- Этажи -----


def get_floors(place: str = "gz") -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM floors WHERE place = ? ORDER BY floor_number",
            (place,),
        ).fetchall()
        return [dict(row) for row in rows]


def get_floor(floor_number: int, place: str = "gz") -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM floors WHERE place = ? AND floor_number = ?",
            (place, floor_number),
        ).fetchone()
        return row_to_dict(row)


def upsert_floor(
    floor_number: int,
    map_path: str,
    meters_per_pixel: float,
    place: str = "gz",
) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO floors(place, floor_number, map_path, meters_per_pixel)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(place, floor_number) DO UPDATE SET
                map_path = excluded.map_path,
                meters_per_pixel = excluded.meters_per_pixel
            """,
            (place, floor_number, map_path, meters_per_pixel),
        )
        conn.commit()


# ----- Метки / локации -----


def get_locations(place: str = "gz") -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT l.*, f.map_path, f.meters_per_pixel
            FROM locations l
            JOIN floors f ON f.place = l.place AND f.floor_number = l.floor
            WHERE l.place = ?
            ORDER BY l.created_at DESC, l.id DESC
            """,
            (place,),
        ).fetchall()
        return [dict(row) for row in rows]


def get_location(location_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT l.*, f.map_path, f.meters_per_pixel
            FROM locations l
            JOIN floors f ON f.place = l.place AND f.floor_number = l.floor
            WHERE l.id = ?
            """,
            (location_id,),
        ).fetchone()
        return row_to_dict(row)


def save_location(
    title: str,
    image_path: str,
    floor: int,
    answer_x: int,
    answer_y: int,
    location_id: int | None = None,
    place: str = "gz",
) -> int:
    with connect() as conn:
        if location_id is None:
            cur = conn.execute(
                """
                INSERT INTO locations(place, title, image_path, answer_x, answer_y, floor)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (place, title.strip(), image_path, answer_x, answer_y, floor),
            )
            new_id = int(cur.lastrowid)
        else:
            conn.execute(
                """
                UPDATE locations
                SET title = ?, image_path = ?, answer_x = ?, answer_y = ?, floor = ?
                WHERE id = ?
                """,
                (title.strip(), image_path, answer_x, answer_y, floor, location_id),
            )
            new_id = location_id
        conn.commit()
        return new_id


def delete_location(location_id: int) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM locations WHERE id = ?", (location_id,))
        conn.commit()


# ----- Результаты последней игры / история -----


def save_game_result(
    score: int, rounds: list[dict[str, Any]], max_score: int = 30
) -> int:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO game_sessions(score, max_score) VALUES (?, ?)",
            (score, max_score),
        )
        session_id = int(cur.lastrowid)
        for index, item in enumerate(rounds, start=1):
            conn.execute(
                """
                INSERT INTO game_session_rounds(
                    session_id, round_number, location_title, image_path,
                    answer_x, answer_y, answer_floor,
                    guessed_x, guessed_y, guessed_floor,
                    distance_meters, points
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    index,
                    item.get("location_title"),
                    item.get("image_path"),
                    item["answer_x"],
                    item["answer_y"],
                    item["answer_floor"],
                    item["guessed_x"],
                    item["guessed_y"],
                    item["guessed_floor"],
                    item["distance_meters"],
                    item["points"],
                ),
            )
        conn.commit()
        return session_id


def get_results(limit: int = 50) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, score, max_score, played_at
            FROM game_sessions
            ORDER BY played_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
