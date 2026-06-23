CREATE TABLE IF NOT EXISTS user_metrics (
    id            TEXT,
    date          DATE,
    page_flips    INTEGER,
    reading_time  FLOAT,
    ig_time       FLOAT,
    PRIMARY KEY (id, date)
);
