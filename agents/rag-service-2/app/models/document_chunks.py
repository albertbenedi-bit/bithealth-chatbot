# rag-service/app/models/document_chunks.py

# Import SQLAlchemy components
from sqlalchemy import Column, Integer, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Import pgvector support for SQLAlchemy
from pgvector.sqlalchemy import Vector

# This base class is needed by SQLAlchemy's declarative approach
# In your dependencies.py, you created a Base = declarative_base()
# Ensure you use the *same* Base instance across your application if defining
# models in different files. A common pattern is to define the Base in
# a shared location like app/core/base.py and import it everywhere.
# For simplicity here, we'll assume Base is imported from dependencies.py
# or define it here if this is the only place models are defined.

# Assuming Base is defined in app/core/dependencies.py or app/core/base.py
from app.core.dependencies import Base # Or from app.core.base import Base

# Define the table name for your document chunks
DOCUMENT_CHUNKS_TABLE_NAME = "document_chunks"

# Define the SQLAlchemy model for the document_chunks table
class DocumentChunk(Base):
    """SQLAlchemy model representing a document chunk stored in PGVector."""
    __tablename__ = DOCUMENT_CHUNKS_TABLE_NAME

    id = Column(Integer, primary_key=True, index=True)
    # Store the text content of the chunk
    content = Column(Text, nullable=False)
    # Store the vector embedding. Dimension (e.g., 384) must match your embedding model.
    # Check the dimension of the SentenceTransformer model you are using.
    embedding = Column(Vector(384), nullable=False) # !!! IMPORTANT: Replace 384 with actual dimension !!!
    # Store metadata about the chunk, e.g., source file, page number
    source = Column(Text, index=True) # Example metadata field

    # You could add other metadata fields here, e.g.:
    # page_number = Column(Integer)
    # document_id = Column(Integer) # If tracking full documents


# --- How this model is used ---
# 1. In your Indexing Workflow (indexing-workflow/scripts/index_documents.py):
#    You will use SQLAlchemy sessions (obtained from your engine/SessionLocal)
#    and this DocumentChunk model to create and insert rows into the database.
#    e.g., session.add(DocumentChunk(content=..., embedding=..., source=...))

# 2. In app/core/dependencies.py (implicitly by PGVector):
#    Langchain's PGVector class uses SQLAlchemy internally and needs to know
#    the table structure to perform operations. By passing the connection string
#    and collection name, Langchain handles the ORM interaction based on its
#    understanding of how to use PGVector with SQLAlchemy models.

# 3. Potentially in your RAG service code (though less common with Langchain):
#    If you needed to perform direct SQL queries or manipulate chunks beyond
#    Langchain's retrieval methods, you would use sessions and this model here.