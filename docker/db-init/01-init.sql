-- Runs once on first database boot.
-- Enables the pgvector extension so Vektra's Vector(768) columns work.
CREATE EXTENSION IF NOT EXISTS vector;