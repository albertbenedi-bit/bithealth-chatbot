import os
import sys
import logging

try:
    from langchain_community.vectorstores.pgvector import PGVector
    from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_huggingface import HuggingFaceEmbeddings
    import psycopg2
except ImportError as e:
    print(f"Error: A required library is not installed. Please run 'pip install langchain-community pgvector psycopg2-binary sentence-transformers pypdf langchain-huggingface'. Details: {e}")
    sys.exit(1)

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_db_connection_string():
    """
    Constructs the database connection string from environment variables.
    This should match the credentials used by your RAG service.
    """
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "BTxg8LN5lH") # Default from secret.sh
    db_host = os.getenv("POSTGRES_HOST", "localhost") # Default to localhost for port-forward
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "rag_db")
    
    # This connection string is for psycopg2, which PGVector uses under the hood
    return f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

def clear_collection(conn_str: str, collection_name: str):
    """Deletes all documents from a specific collection to ensure a fresh start."""
    logging.info(f"Attempting to clear old documents from collection '{collection_name}'...")
    try:
        # PGVector stores collection metadata in 'langchain_pg_collection'
        # The original connection string is for SQLAlchemy. psycopg2 needs a pure postgresql URI.
        psycopg2_conn_str = conn_str.replace("+psycopg2", "")
        with psycopg2.connect(psycopg2_conn_str) as conn:
            with conn.cursor() as cur:
                # First, check if the collection table even exists to avoid warnings on the first run.
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'langchain_pg_collection'
                    );
                """)
                if not cur.fetchone()[0]:
                    logging.info("LangChain collection table not found, no need to clear. It will be created during ingestion.")
                    return

                # If the table exists, get the UUID of the collection to clear its embeddings.
                cur.execute("SELECT uuid FROM langchain_pg_collection WHERE name = %s", (collection_name,))
                collection_uuid_row = cur.fetchone()
                if collection_uuid_row:
                    collection_uuid = collection_uuid_row[0]
                    # Delete all embeddings associated with that collection from the embedding table.
                    cur.execute("DELETE FROM langchain_pg_embedding WHERE collection_id = %s", (collection_uuid,))
                    logging.info(f"Successfully cleared {cur.rowcount} old document chunks from collection '{collection_name}'.")
                else:
                    logging.info(f"Collection '{collection_name}' not found, no need to clear.")
    except Exception as e:
        logging.error(f"An unexpected error occurred while trying to clear the collection: {e}")

def main():
    logging.info("Starting data ingestion process...")
    
    try:
        # 1. Define the collection name (must match what the RAG service uses)
        collection_name = "chatbot_documents"
        
        # 2. Load documents from the specified directory
        # The path is relative to where the script is run (e.g., from the 'iac' directory)
        data_path = './postgres/knowledge_data/'
        logging.info(f"Loading documents from {data_path}...")
        txt_loader = DirectoryLoader(data_path, glob="**/*.txt", loader_cls=TextLoader, show_progress=True, use_multithreading=True)
        pdf_loader = DirectoryLoader(data_path, glob="**/*.pdf", loader_cls=PyPDFLoader, show_progress=True, use_multithreading=True)
        
        documents = txt_loader.load() + pdf_loader.load()

        if not documents:
            logging.warning(f"No .txt or .pdf documents found in '{data_path}'. Exiting.")
            sys.exit(0)
        logging.info(f"Loaded {len(documents)} document(s).")

        # 3. Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        docs = text_splitter.split_documents(documents)
        logging.info(f"Split documents into {len(docs)} chunks.")

        # 4. Initialize the same embedding model used by the RAG service
        logging.info("Initializing embedding model: all-MiniLM-L6-v2")
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        # 5. Get DB connection string and ingest data into PGVector
        connection_string = get_db_connection_string()
        logging.info(f"Connecting to database and ingesting documents into collection '{collection_name}'...")

        # 6. Clear any old data from the collection before ingesting new data
        clear_collection(connection_string, collection_name)
        
        PGVector.from_documents(
            embedding=embeddings,
            documents=docs,
            collection_name=collection_name,
            connection_string=connection_string,
        )
        logging.info("✅ Data ingestion complete!")

    except Exception as e:
        logging.error(f"An error occurred during data ingestion: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
