from __future__ import annotations
import numpy as np
from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy import text, bindparam
from pgvector.sqlalchemy import Vector

DIM = 384

def _as_list(v: np.ndarray | list[float] | None) -> list[float]:
    if v is None:
        return [0.0] * DIM
    if isinstance(v, np.ndarray):
        return v.astype("float32").tolist()
    return list(v)

def _is_zero(v: np.ndarray) -> bool:
    return float(np.linalg.norm(v)) == 0.0

def similar_events(conn, query_vec: np.ndarray, limit: int = 20) -> List[Dict[str, Any]]:
    if _is_zero(query_vec):
        # fallback: upcoming soonest
        sql = text("""
            SELECT id, title, start_time, location, tags, 0.0 AS score
            FROM events
            WHERE start_time > NOW()
            ORDER BY start_time ASC
            LIMIT :lim
        """)
        rows = conn.execute(sql, {"lim": limit}).mappings().all()
        return [dict(r) for r in rows]

    sql = text("""
        SELECT id, title, start_time, location, tags,
               1 - (embed <=> :q) AS score
        FROM events
        WHERE start_time > NOW()
        ORDER BY embed <=> :q
        LIMIT :lim
    """).bindparams(bindparam("q", type_=Vector(DIM)))
    rows = conn.execute(sql, {"q": _as_list(query_vec), "lim": limit}).mappings().all()
    return [dict(r) for r in rows]

def user_feed(conn, user_vec: np.ndarray, limit: int = 20) -> List[Dict[str, Any]]:
    base = similar_events(conn, user_vec, limit=limit * 2)
    now = datetime.now(timezone.utc)
    def rerank(ev):
        dt_days = max(0.0, (ev["start_time"] - now).total_seconds() / 86400.0)
        time_bonus = max(0.0, 1.0 - dt_days / 14.0)
        return 0.7 * float(ev.get("score", 0.0)) + 0.3 * time_bonus
    base.sort(key=rerank, reverse=True)
    return base[:limit]


def similar_events(conn, query_vec: np.ndarray, limit: int = 20) -> List[Dict[str, Any]]:
    if _is_zero(query_vec):
        sql = text("""
            SELECT id, title, description, start_time, location, tags, 0.0 AS score
            FROM events
            WHERE start_time > NOW()
            ORDER BY start_time ASC
            LIMIT :lim
        """)
        rows = conn.execute(sql, {"lim": limit}).mappings().all()
        return [dict(r) for r in rows]

    sql = text("""
        SELECT id, title, description, start_time, location, tags,
               1 - (embed <=> :q) AS score
        FROM events
        WHERE start_time > NOW()
        ORDER BY embed <=> :q
        LIMIT :lim
    """).bindparams(bindparam("q", type_=Vector(DIM)))
    rows = conn.execute(sql, {"q": _as_list(query_vec), "lim": limit}).mappings().all()
    return [dict(r) for r in rows]
