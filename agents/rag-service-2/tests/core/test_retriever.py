import pytest
from unittest.mock import MagicMock
from langchain_core.documents import Document

# Import the class for spec'ing the mock
from langchain_community.vectorstores.pgvector import PGVector
# The class to be tested
from app.core.retriever import PGVectorRetriever

@pytest.fixture
def mock_pgvector_store():
    """Fixture for a mocked PGVector store instance."""
    # Use spec=PGVector to ensure the mock passes 'isinstance' checks
    return MagicMock(spec=PGVector)

def test_retriever_initialization(mock_pgvector_store):
    """Tests that the PGVectorRetriever initializes correctly."""
    retriever = PGVectorRetriever(pgvector_store=mock_pgvector_store)
    assert retriever._vector_store is mock_pgvector_store

def test_retriever_init_raises_type_error():
    """Tests that initialization fails with the wrong store type."""
    with pytest.raises(TypeError):
        PGVectorRetriever(pgvector_store="not a pgvector store")

def test_retrieve_similarity_search(mock_pgvector_store):
    """Tests the retrieve method with search_type='similarity'."""
    # Arrange
    mock_docs = [Document(page_content="test")]
    mock_pgvector_store.similarity_search.return_value = mock_docs
    retriever = PGVectorRetriever(pgvector_store=mock_pgvector_store)
    
    # Act
    result = retriever.retrieve("test query", k=3, search_type="similarity")
    
    # Assert
    mock_pgvector_store.similarity_search.assert_called_once_with("test query", k=3)
    mock_pgvector_store.max_marginal_relevance_search.assert_not_called()
    assert result == mock_docs

def test_retrieve_mmr_search(mock_pgvector_store):
    """Tests the retrieve method with search_type='mmr'."""
    # Arrange
    mock_docs = [Document(page_content="test mmr")]
    mock_pgvector_store.max_marginal_relevance_search.return_value = mock_docs
    retriever = PGVectorRetriever(pgvector_store=mock_pgvector_store)
    
    # Act
    result = retriever.retrieve("test query", k=5, search_type="mmr")
    
    # Assert
    mock_pgvector_store.max_marginal_relevance_search.assert_called_once_with("test query", k=5)
    mock_pgvector_store.similarity_search.assert_not_called()
    assert result == mock_docs