import os
import time

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("Error: psycopg2-binary is not installed. Please install it using 'pip install psycopg2-binary'")
    exit(1)

from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# --- Database Connection Details ---
# Read from environment variables with sensible defaults for local execution.
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "BTxg8LN5lH")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME_TO_CREATE = os.getenv("POSTGRES_DB", "rag_db") #hr_rag_db

def create_database_and_tables():
    """
    Connects to PostgreSQL, creates the specified database if it doesn't exist,
    and then creates the necessary tables and indexes.
    """
    conn = None
    cur = None
    try:
        # --- 1. Connect to the default 'postgres' database to create our new DB (with retries) ---
        print(f"Attempting to connect to PostgreSQL at {DB_HOST}:{DB_PORT}...")
        for attempt in range(5):
            try:
                conn = psycopg2.connect(
                    dbname="postgres",
                    user=DB_USER,
                    password=DB_PASSWORD,
                    host=DB_HOST,
                    port=DB_PORT
                )
                print("Successfully connected to PostgreSQL.")
                break
            except psycopg2.OperationalError as e:
                print(f"Connection attempt {attempt + 1} failed: {e}. Retrying in 5 seconds...")
                time.sleep(5)
        else:
            print("Could not connect to PostgreSQL after several attempts. Aborting.")
            return

        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # --- 2. Check if the target database exists ---
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME_TO_CREATE,))
        exists = cur.fetchone()

        # --- 3. Create the database if it does not exist ---
        if not exists:
            print(f"Database '{DB_NAME_TO_CREATE}' does not exist. Creating it...")
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME_TO_CREATE)))
            print(f"Database '{DB_NAME_TO_CREATE}' created successfully.")
        else:
            print(f"Database '{DB_NAME_TO_CREATE}' already exists.")

    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL or creating database: {e}")
        return
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    # --- 4. Connect to the new database to create tables ---
    try:
        print(f"\nConnecting to the '{DB_NAME_TO_CREATE}' database...")
        conn = psycopg2.connect(
            dbname=DB_NAME_TO_CREATE,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()

        # --- 5. Create the 'vector' extension ---
        print("Creating 'vector' extension if it doesn't exist...")
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("'vector' extension is ready.")

        # --- 6. Define and create the 'documents' table ---
        print("Creating 'documents' table...")
        documents_table_sql = """
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
        """
        cur.execute(documents_table_sql)
        print("'documents' table created successfully.")

        # --- 7. Define and create the 'document_chunks' table ---
        # Adjust the embedding size to 1536 (default) for OpenAI embeddings
        print("Creating 'document_chunks' table...")
        document_chunks_table_sql = """
        CREATE TABLE IF NOT EXISTS document_chunks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            chunk_content TEXT NOT NULL,
            embedding VECTOR(384) NOT NULL, -- Dimension for all-MiniLM-L6-v2 is 384
            chunk_number INTEGER NOT NULL,
            start_index INTEGER,
            end_index INTEGER,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            metadatas JSONB
        );
        """
        cur.execute(document_chunks_table_sql)
        print("'document_chunks' table created successfully.")

        # --- 8. Create indexes ---
        print("Creating indexes on 'document_chunks' table...")

        # Index for foreign key for faster joins and lookups by document
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_document_id
            ON document_chunks (document_id);
        """)
        print("Index 'idx_document_id' created.")

        # IVFFlat index for Approximate Nearest Neighbor (ANN) search
        # Note: For a balance of build time, search speed, and recall, HNSW is often preferred.
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_embedding_ivfflat
            ON document_chunks
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """)
        print("Index 'idx_embedding_ivfflat' (IVFFlat) created.")

        # --- 9. Commit the changes ---
        conn.commit()
        print("\nAll tables and indexes created successfully. Changes have been committed.")

    except psycopg2.Error as e:
        print(f"\nAn error occurred during table creation: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
        print("Database connection closed.")

if __name__ == "__main__":
    create_database_and_tables()
