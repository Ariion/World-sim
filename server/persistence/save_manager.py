"""
GENESIS ENGINE — persistence/save_manager.py
Snapshots périodiques vers PostgreSQL.
Le monde survit aux redémarrages serveur.
"""
import json
import asyncio
import asyncpg
from datetime import datetime

from ..config import DATABASE_URL, SNAPSHOT_INTERVAL_TICKS


class SaveManager:
    def __init__(self):
        self._pool: asyncpg.Pool | None = None

    async def connect(self):
        try:
            self._pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
            await self._init_schema()
            print("[SaveManager] Connecté à PostgreSQL ✓")
        except Exception as e:
            print(f"[SaveManager] PostgreSQL indisponible ({e}) — mode mémoire seule")
            self._pool = None

    async def _init_schema(self):
        if not self._pool:
            return
        async with self._pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS world_snapshots (
                    id          SERIAL PRIMARY KEY,
                    tick        INTEGER NOT NULL,
                    year_bp     INTEGER NOT NULL,
                    snapshot    JSONB   NOT NULL,
                    created_at  TIMESTAMP DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS prayers (
                    id          SERIAL PRIMARY KEY,
                    prayer_id   INTEGER NOT NULL,
                    tribe_id    INTEGER,
                    tribe_name  TEXT,
                    text        TEXT,
                    intensity   FLOAT,
                    year_bp     INTEGER,
                    tick        INTEGER,
                    answered    BOOLEAN DEFAULT FALSE,
                    created_at  TIMESTAMP DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS events (
                    id          SERIAL PRIMARY KEY,
                    tick        INTEGER,
                    year_bp     INTEGER,
                    event_type  TEXT,
                    text        TEXT,
                    created_at  TIMESTAMP DEFAULT NOW()
                );
            """)

    async def save_snapshot(self, world_state) -> bool:
        if not self._pool:
            return False
        try:
            snapshot = world_state.to_snapshot()
            async with self._pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO world_snapshots (tick, year_bp, snapshot) VALUES ($1, $2, $3)",
                    world_state.time.tick,
                    world_state.time.year_bp,
                    json.dumps(snapshot),
                )
            return True
        except Exception as e:
            print(f"[SaveManager] Erreur snapshot: {e}")
            return False

    async def load_latest(self) -> dict | None:
        if not self._pool:
            return None
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT snapshot FROM world_snapshots ORDER BY tick DESC LIMIT 1"
                )
                if row:
                    return json.loads(row["snapshot"])
        except Exception as e:
            print(f"[SaveManager] Erreur chargement: {e}")
        return None

    async def log_event(self, tick: int, year_bp: int, event_type: str, text: str):
        if not self._pool:
            return
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO events (tick, year_bp, event_type, text) VALUES ($1,$2,$3,$4)",
                    tick, year_bp, event_type, text,
                )
        except Exception:
            pass

    async def save_prayer(self, prayer: dict):
        if not self._pool:
            return
        try:
            async with self._pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO prayers (prayer_id, tribe_id, tribe_name, text, intensity, year_bp, tick)
                    VALUES ($1,$2,$3,$4,$5,$6,$7)
                    ON CONFLICT DO NOTHING
                """,
                    prayer["id"], prayer.get("tribe_id"), prayer.get("tribe_name"),
                    prayer["text"], prayer["intensity"], prayer.get("year_bp"), prayer.get("tick"),
                )
        except Exception:
            pass


save_manager = SaveManager()
