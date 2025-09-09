# rag-service/app/models/rag.py

from pydantic import BaseModel
from typing import List, Optional

# Model for the incoming user question in the /ask endpoint request body
class Question(BaseModel):
    """Represents a user's question."""
    text: str # The actual text of the user's question

    class Config:
        # Example for OpenAPI documentation
        json_schema_extra = {
            "example": {
                "text": "What is the company's vacation policy?"
            }
        }

# Model for the outgoing response from the /ask endpoint
class Answer(BaseModel):
    """Represents the AI's answer and source information for the API."""
    text: str # The generated answer text
    sources: List[str] # A list of source identifiers (e.g., filenames, page numbers)

    class Config:
        # Example for OpenAPI documentation
        json_schema_extra = {
            "example": {
                "text": "According to document 'policy.pdf', employees are entitled to 15 vacation days per year.",
                "sources": ["policy.pdf", "handbook.docx"]
            }
        }

# Model for the internal result of the RAG service
class RAGResult(BaseModel):
    """Represents the internal result from the RAGService."""
    text: str
    sources: List[str]

# You could add other API models here if needed for other endpoints
# e.g., for an indexing request body:
# class IndexRequest(BaseModel):
#     document_path: str # Path to the document to index
#     # etc.