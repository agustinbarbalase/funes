CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS ephemerides (
  id          SERIAL PRIMARY KEY,
  day         SMALLINT    NOT NULL,
  month       SMALLINT    NOT NULL,
  year        SMALLINT,
  type        VARCHAR(50) NOT NULL,
  title       VARCHAR(500) NOT NULL,
  description TEXT        NOT NULL,
  images      TEXT[]      DEFAULT '{}',
  urls        TEXT[]      DEFAULT '{}',
  embedding   VECTOR(384)
);

CREATE INDEX ix_ephemerides_day_month ON ephemerides (day, month);

CREATE INDEX ix_ephemerides_embedding
  ON ephemerides
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
