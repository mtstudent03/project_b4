CREATE TABLE IF NOT EXISTS user_metrics (
    id            TEXT,
    date          DATE,
    yt_time       FLOAT,
    page_flips    INTEGER,
    reading_time  FLOAT,
    ig_time       FLOAT,
    concentration INTEGER,
    PRIMARY KEY (id, date)
);

