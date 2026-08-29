-- =========================================================
-- RFP Evaluation & Supplier Ranking — SQLite schema
-- =========================================================

CREATE TABLE IF NOT EXISTS evaluation_criteria (
    criterion_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    description     TEXT NOT NULL,
    weight          REAL NOT NULL,      -- percentage, active weights must sum to 100
    max_score       INTEGER NOT NULL DEFAULT 10,
    is_active       INTEGER NOT NULL DEFAULT 1,   -- 1 = active, 0 = inactive
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS rfp_runs (
    rfp_run_id      TEXT PRIMARY KEY,   -- UUID
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    status          TEXT NOT NULL DEFAULT 'in_progress',  -- in_progress | completed | failed
    criteria_snapshot TEXT,             -- JSON snapshot of active criteria used for this run
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS supplier_results (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    rfp_run_id          TEXT NOT NULL,
    supplier_name       TEXT NOT NULL,
    submission_date     TEXT NOT NULL,      -- ISO date, used in tie-break
    experience_rating   REAL NOT NULL,      -- historical experience rating, used in tie-break
    absolute_score      REAL NOT NULL,      -- weighted absolute score (0-100)
    ppi                 REAL NOT NULL,      -- Peer Performance Index (0-100)
    final_rank          INTEGER NOT NULL,
    result_json         TEXT NOT NULL,      -- full per-criterion breakdown, evidence, warnings
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (rfp_run_id) REFERENCES rfp_runs (rfp_run_id)
);

CREATE INDEX IF NOT EXISTS idx_supplier_results_run ON supplier_results (rfp_run_id);
