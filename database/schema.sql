-- GENESIS ENGINE — database/schema.sql
-- Structure PostgreSQL complète.
-- Créée automatiquement au démarrage, mais gardée ici pour référence.

CREATE TABLE IF NOT EXISTS world_snapshots (
    id          SERIAL PRIMARY KEY,
    tick        INTEGER      NOT NULL,
    year_bp     INTEGER      NOT NULL,
    snapshot    JSONB        NOT NULL,
    created_at  TIMESTAMP    DEFAULT NOW()
);

-- Index pour accès rapide au dernier snapshot
CREATE INDEX IF NOT EXISTS idx_snapshots_tick ON world_snapshots(tick DESC);

-- Garder seulement les 100 derniers snapshots (cleanup via cron ou trigger)
CREATE TABLE IF NOT EXISTS prayers (
    id          SERIAL PRIMARY KEY,
    prayer_id   INTEGER      NOT NULL UNIQUE,
    tribe_id    INTEGER,
    tribe_name  TEXT,
    text        TEXT,
    intensity   FLOAT,
    year_bp     INTEGER,
    tick        INTEGER,
    answered    BOOLEAN      DEFAULT FALSE,
    created_at  TIMESTAMP    DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS events (
    id          SERIAL PRIMARY KEY,
    tick        INTEGER,
    year_bp     INTEGER,
    event_type  TEXT,
    text        TEXT,
    created_at  TIMESTAMP    DEFAULT NOW()
);

-- Vue pratique : événements récents
CREATE OR REPLACE VIEW recent_events AS
    SELECT * FROM events ORDER BY tick DESC LIMIT 100;

-- Vue : prières non répondues
CREATE OR REPLACE VIEW unanswered_prayers AS
    SELECT * FROM prayers WHERE answered = FALSE ORDER BY created_at DESC;
