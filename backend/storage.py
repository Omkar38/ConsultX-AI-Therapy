from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime
from typing import Generator, List, Optional

from .models import (
    BufferSnapshot,
    MessageRecord,
    RiskTier,
    SessionMetrics,
    SessionRecord,
    SessionStatus,
    SenderRole,
    utc_now,
)


class SessionStorage:
    """SQLite-backed persistence layer for sessions and messages."""

    def __init__(self, db_path: str = "consultx.db") -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialise()

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _initialise(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    active_risk_tier TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    content TEXT NOT NULL,
                    sentiment_score REAL NOT NULL,
                    risk_tier TEXT NOT NULL,
                    risk_score REAL NOT NULL,
                    flagged_keywords TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                );

                CREATE TABLE IF NOT EXISTS session_metrics (
                    session_id TEXT PRIMARY KEY,
                    message_count INTEGER NOT NULL,
                    user_turns INTEGER NOT NULL,
                    assistant_turns INTEGER NOT NULL,
                    avg_sentiment REAL NOT NULL,
                    max_risk_tier TEXT NOT NULL,
                    tier_counts TEXT NOT NULL,
                    band_counts TEXT NOT NULL,
                    trend_notes TEXT NOT NULL,
                    suggested_resources TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                );

                CREATE TABLE IF NOT EXISTS buffers (
                    session_id TEXT PRIMARY KEY,
                    serialized_buffer TEXT NOT NULL,
                    capacity INTEGER NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                );
                """
            )

    # Session operations -------------------------------------------------

    def create_session(self, session: SessionRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO sessions (id, user_id, status, created_at, updated_at, active_risk_tier, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session.id,
                    session.user_id,
                    session.status.value,
                    session.created_at.isoformat(),
                    session.updated_at.isoformat(),
                    session.active_risk_tier.value,
                    json.dumps(session.metadata),
                ),
            )

    def update_session(
        self,
        session_id: str,
        *,
        status: Optional[SessionStatus] = None,
        active_risk_tier: Optional[RiskTier] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        updates = []
        params: List[object] = []
        if status:
            updates.append("status = ?")
            params.append(status.value)
        if active_risk_tier:
            updates.append("active_risk_tier = ?")
            params.append(active_risk_tier.value)
        if metadata is not None:
            updates.append("metadata = ?")
            params.append(json.dumps(metadata))
        updates.append("updated_at = ?")
        params.append(utc_now().isoformat())
        params.append(session_id)

        with self._connect() as conn:
            conn.execute(
                f"UPDATE sessions SET {', '.join(updates)} WHERE id = ?",
                params,
            )

    def get_session(self, session_id: str) -> Optional[SessionRecord]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
        if not row:
            return None
        return _row_to_session(row)

    def list_sessions(
        self,
        *,
        user_id: Optional[str] = None,
        status: Optional[SessionStatus] = None,
    ) -> List[SessionRecord]:
        query = "SELECT * FROM sessions"
        clauses = []
        params: List[object] = []

        if user_id:
            clauses.append("user_id = ?")
            params.append(user_id)
        if status:
            clauses.append("status = ?")
            params.append(status.value)

        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY datetime(created_at) DESC"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [_row_to_session(row) for row in rows]

    # Message operations --------------------------------------------------

    def insert_message(self, message: MessageRecord) -> MessageRecord:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO messages (
                    session_id, sender, content, sentiment_score,
                    risk_tier, risk_score, flagged_keywords, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message.session_id,
                    message.sender.value,
                    message.content,
                    message.sentiment_score,
                    message.risk_tier.value,
                    message.risk_score,
                    json.dumps(message.flagged_keywords),
                    message.created_at.isoformat(),
                ),
            )
            message_id = cursor.lastrowid
        message.id = message_id
        return message

    def list_messages(self, session_id: str) -> List[MessageRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY id ASC",
                (session_id,),
            ).fetchall()
        return [_row_to_message(row) for row in rows]

    def recent_messages(self, session_id: str, limit: int) -> List[MessageRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM (
                    SELECT * FROM messages
                    WHERE session_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                ) sub
                ORDER BY id ASC
                """,
                (session_id, limit),
            ).fetchall()
        return [_row_to_message(row) for row in rows]

    # Metrics -------------------------------------------------------------

    def upsert_metrics(self, metrics: SessionMetrics) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO session_metrics (
                    session_id, message_count, user_turns, assistant_turns,
                    avg_sentiment, max_risk_tier, tier_counts, band_counts,
                    trend_notes, suggested_resources
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    message_count=excluded.message_count,
                    user_turns=excluded.user_turns,
                    assistant_turns=excluded.assistant_turns,
                    avg_sentiment=excluded.avg_sentiment,
                    max_risk_tier=excluded.max_risk_tier,
                    tier_counts=excluded.tier_counts,
                    band_counts=excluded.band_counts,
                    trend_notes=excluded.trend_notes,
                    suggested_resources=excluded.suggested_resources
                """,
                (
                    metrics.session_id,
                    metrics.message_count,
                    metrics.user_turns,
                    metrics.assistant_turns,
                    metrics.avg_sentiment,
                    metrics.max_risk_tier.value,
                    json.dumps(metrics.tier_counts),
                    json.dumps(metrics.band_counts),
                    json.dumps(metrics.trend_notes),
                    json.dumps(metrics.suggested_resources),
                ),
            )

    def get_metrics(self, session_id: str) -> Optional[SessionMetrics]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM session_metrics WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if not row:
            return None
        return _row_to_metrics(row)

    # Buffer --------------------------------------------------------------

    def save_buffer(self, snapshot: BufferSnapshot) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO buffers (session_id, serialized_buffer, capacity)
                VALUES (?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    serialized_buffer=excluded.serialized_buffer,
                    capacity=excluded.capacity
                """,
                (
                    snapshot.session_id,
                    json.dumps([msg.to_dict() for msg in snapshot.messages]),
                    snapshot.capacity,
                ),
            )

    def load_buffer(self, session_id: str) -> Optional[BufferSnapshot]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM buffers WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if not row:
            return None
        messages = [
            _dict_to_message(rec)
            for rec in json.loads(row["serialized_buffer"] or "[]")
        ]
        return BufferSnapshot(
            session_id=session_id,
            messages=messages,
            capacity=row["capacity"],
        )


# Conversion helpers --------------------------------------------------------


def _row_to_session(row: sqlite3.Row) -> SessionRecord:
    return SessionRecord(
        id=row["id"],
        user_id=row["user_id"],
        status=SessionStatus(row["status"]),
        created_at=_parse_ts(row["created_at"]),
        updated_at=_parse_ts(row["updated_at"]),
        active_risk_tier=RiskTier(row["active_risk_tier"]),
        metadata=json.loads(row["metadata"] or "{}"),
    )


def _row_to_message(row: sqlite3.Row) -> MessageRecord:
    return MessageRecord(
        id=row["id"],
        session_id=row["session_id"],
        sender=SenderRole(row["sender"]),
        content=row["content"],
        sentiment_score=row["sentiment_score"],
        risk_tier=RiskTier(row["risk_tier"]),
        risk_score=row["risk_score"],
        flagged_keywords=json.loads(row["flagged_keywords"] or "[]"),
        created_at=_parse_ts(row["created_at"]),
    )


def _dict_to_message(data: dict) -> MessageRecord:
    return MessageRecord(
        id=data.get("id"),
        session_id=data["session_id"],
        sender=SenderRole(data["sender"]),
        content=data["content"],
        sentiment_score=data["sentiment_score"],
        risk_tier=RiskTier(data["risk_tier"]),
        risk_score=data["risk_score"],
        flagged_keywords=data.get("flagged_keywords", []),
        created_at=_parse_ts(data["created_at"]),
    )


def _row_to_metrics(row: sqlite3.Row) -> SessionMetrics:
    return SessionMetrics(
        session_id=row["session_id"],
        message_count=row["message_count"],
        user_turns=row["user_turns"],
        assistant_turns=row["assistant_turns"],
        avg_sentiment=row["avg_sentiment"],
        max_risk_tier=RiskTier(row["max_risk_tier"]),
        tier_counts=json.loads(row["tier_counts"] or "{}"),
        band_counts=json.loads(row["band_counts"] or "{}"),
        trend_notes=json.loads(row["trend_notes"] or "[]"),
        suggested_resources=json.loads(row["suggested_resources"] or "[]"),
    )


def _parse_ts(value: str):
    # Use fromisoformat with fallback for Z suffix.
    if value.endswith("Z"):
        value = value.replace("Z", "+00:00")
    return datetime.fromisoformat(value)
