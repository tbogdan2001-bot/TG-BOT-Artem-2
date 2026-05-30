# database.py
# Слой хранения для клубной воронки (club3-сценарий).
# Хранит шаг сценария пользователя и флаги (заявка/доступ/подписка) в SQLite.

import os
import logging
from datetime import datetime, timezone

import aiosqlite

import config

DB_PATH = os.path.join(config.BASE_DIR, "funnel_bot.db")

logger = logging.getLogger(__name__)

_db_connection: aiosqlite.Connection | None = None


def get_db() -> aiosqlite.Connection:
    if _db_connection is None:
        raise RuntimeError("Database connection not initialized. Call init_db() first.")
    return _db_connection


async def close_db() -> None:
    global _db_connection
    if _db_connection is not None:
        await _db_connection.close()
        _db_connection = None
        logger.info("Database connection closed.")


async def init_db() -> None:
    """Создаёт соединение и таблицу пользователей."""
    global _db_connection
    if _db_connection is None:
        _db_connection = await aiosqlite.connect(DB_PATH)

    db = get_db()
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            telegram_id      INTEGER PRIMARY KEY,
            username         TEXT,
            subid            TEXT,
            scenario_step    TEXT DEFAULT 'started',
            club_flow_allowed INTEGER DEFAULT 0,
            join_requested   INTEGER DEFAULT 0,
            subscribed       INTEGER DEFAULT 0,
            created_at       TEXT NOT NULL,
            updated_at       TEXT NOT NULL
        )
        """
    )
    await db.commit()
    logger.info("Database initialized at %s", DB_PATH)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def add_or_update_user(telegram_id: int, username: str | None = None,
                             subid: str | None = None) -> None:
    """Создаёт пользователя или обновляет его username/subid, сбрасывая шаг на 'started'."""
    db = get_db()
    now = _now()
    existing = await get_user(telegram_id)
    if existing is None:
        await db.execute(
            "INSERT INTO users (telegram_id, username, subid, scenario_step, created_at, updated_at) "
            "VALUES (?, ?, ?, 'started', ?, ?)",
            (telegram_id, username, subid or "", now, now),
        )
    else:
        await db.execute(
            "UPDATE users SET username = COALESCE(?, username), "
            "subid = CASE WHEN ?<>'' THEN ? ELSE subid END, "
            "scenario_step = 'started', updated_at = ? WHERE telegram_id = ?",
            (username, subid or "", subid or "", now, telegram_id),
        )
    await db.commit()


async def get_user(telegram_id: int) -> dict | None:
    db = get_db()
    db.row_factory = aiosqlite.Row
    async with db.execute(
        "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
    ) as cursor:
        row = await cursor.fetchone()
    return dict(row) if row else None


async def _set_field(telegram_id: int, field: str, value) -> None:
    db = get_db()
    await db.execute(
        f"UPDATE users SET {field} = ?, updated_at = ? WHERE telegram_id = ?",
        (value, _now(), telegram_id),
    )
    await db.commit()


async def set_scenario_step(telegram_id: int, step: str) -> None:
    await _set_field(telegram_id, "scenario_step", step)


async def set_club_flow_allowed(telegram_id: int, allowed: bool) -> None:
    await _set_field(telegram_id, "club_flow_allowed", 1 if allowed else 0)


async def set_join_requested(telegram_id: int, requested: bool) -> None:
    await _set_field(telegram_id, "join_requested", 1 if requested else 0)


async def set_subscribed(telegram_id: int, subscribed: bool) -> None:
    await _set_field(telegram_id, "subscribed", 1 if subscribed else 0)


async def get_stats() -> dict:
    """Сводка по шагам воронки для /admin."""
    db = get_db()
    db.row_factory = aiosqlite.Row

    async def _count(where: str = "", params: tuple = ()) -> int:
        sql = "SELECT COUNT(*) AS c FROM users"
        if where:
            sql += f" WHERE {where}"
        async with db.execute(sql, params) as cur:
            r = await cur.fetchone()
        return r["c"] if r else 0

    total = await _count()
    joined = await _count("join_requested = 1")
    not_robot = await _count("scenario_step IN ('club3_step2_sent', 'club3_step3_sent', 'club3_reviews_clicked')")
    reviews = await _count("scenario_step = 'club3_reviews_clicked'")

    by_step: dict[str, int] = {}
    async with db.execute(
        "SELECT scenario_step, COUNT(*) AS c FROM users GROUP BY scenario_step"
    ) as cur:
        async for row in cur:
            by_step[row["scenario_step"] or "unknown"] = row["c"]

    return {
        "total": total,
        "joined": joined,
        "not_robot": not_robot,
        "reviews": reviews,
        "by_step": by_step,
    }
