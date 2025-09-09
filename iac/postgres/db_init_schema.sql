-- =================================================================
--  PostgreSQL database schema for the HR RAG Chatbot
--  Database: hr_rag_db
--
--  Instructions:
--  1. Manually create the 'hr_rag_db' database first.
--     From your terminal (e.g., using psql or a GUI tool):
--     > psql -U postgres -c "CREATE DATABASE hr_rag_db"
--
--  2. Connect to the new database and run this script.
--     From your terminal:
--     > psql -U postgres -d hr_rag_db -f path/to/this/db_init_schema.sql
-- =================================================================

-- Enable the pgvector extension if it's not already enabled.
-- This must be done once per database.
CREATE EXTENSION IF NOT EXISTS vector;


-- === TABLES ===

-- Table to store metadata about each ingested source document.
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    source_url TEXT,
    ingestion_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL DEFAULT 'ingested',
    metadatas JSONB,
    checksum VARCHAR(64) UNIQUE
);

COMMENT ON TABLE documents IS 'Stores metadata about ingested source documents.';
COMMENT ON COLUMN documents.checksum IS 'SHA256 checksum of the file content to prevent duplicate ingestion.';
COMMENT ON COLUMN documents.status IS 'The current status of the document in the ingestion pipeline (e.g., ingested, chunked, failed).';


-- Table to store individual document chunks and their vector embeddings.
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_content TEXT NOT NULL,
    embedding VECTOR(384) NOT NULL, -- Dimension for all-MiniLM-L6-v2 is 384; VECTOR(1536) is the vector dimension for OpenAI's text-embedding-ada-002.
    chunk_number INTEGER NOT NULL,
    start_index INTEGER,
    end_index INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadatas JSONB
);

COMMENT ON TABLE document_chunks IS 'Stores text chunks from documents, their vector embeddings, and associated metadata.';
COMMENT ON COLUMN document_chunks.embedding IS 'The vector embedding for the chunk_content, with a dimension of 384 for all-MiniLM-L6-v2.';


-- === INDEXES ===

-- Create an index on the foreign key for faster joins and lookups by document.
CREATE INDEX IF NOT EXISTS idx_document_id ON document_chunks (document_id);

-- Create an IVFFlat index for Approximate Nearest Neighbor (ANN) search on embeddings.
-- The operator class 'vector_cosine_ops' is specified for cosine similarity searches.
CREATE INDEX IF NOT EXISTS idx_embedding_ivfflat ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);