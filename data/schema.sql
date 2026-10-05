
CREATE TABLE IF NOT EXISTS architects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    architect_name TEXT,
    architecture_id TEXT,
    registration_number TEXT,
    registration_year INTEGER,
    address TEXT,
    state TEXT,
    city TEXT,
    pincode TEXT,
    phone TEXT,
    email TEXT,
    registration_status TEXT,
    valid_upto TEXT,
    source_url TEXT NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'directory',
    record_scope TEXT,
    extracted_at TEXT NOT NULL,
    processing_status TEXT NOT NULL DEFAULT 'success',
    duplicate_status TEXT NOT NULL DEFAULT 'unique',
    error_info TEXT,
    raw_hash TEXT,
    UNIQUE(registration_number, source_url)
);
CREATE INDEX IF NOT EXISTS idx_arch_reg ON architects(registration_number);
CREATE INDEX IF NOT EXISTS idx_arch_city ON architects(city);
CREATE INDEX IF NOT EXISTS idx_arch_state ON architects(state);
CREATE INDEX IF NOT EXISTS idx_arch_status ON architects(processing_status);

CREATE TABLE IF NOT EXISTS extraction_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    query_value TEXT,
    status TEXT NOT NULL,
    total_identified INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    pending_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    duplicate_count INTEGER DEFAULT 0,
    captcha_count INTEGER DEFAULT 0,
    started_at TEXT,
    latest_activity TEXT,
    finished_at TEXT,
    records_per_second REAL DEFAULT 0,
    last_cursor TEXT,
    error_info TEXT
);

CREATE TABLE IF NOT EXISTS extraction_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    event_type TEXT NOT NULL,
    message TEXT,
    url TEXT,
    http_status INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY(job_id) REFERENCES extraction_jobs(id)
);

CREATE TABLE IF NOT EXISTS raw_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    url TEXT NOT NULL,
    response_hash TEXT,
    status_code INTEGER,
    captured_at TEXT NOT NULL,
    content TEXT,
    FOREIGN KEY(job_id) REFERENCES extraction_jobs(id)
);
