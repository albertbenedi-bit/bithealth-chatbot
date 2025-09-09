import pytest
from unittest.mock import MagicMock
from langchain_core.documents import Document

# The class to be tested
from app.core.rag_service import RAGService
from app.models.rag import RAGResult

# Mock dependencies
@pytest.fixture
def mock_retriever():
    """Mocks the PGVectorRetriever."""
    return MagicMock()

@pytest.fixture
def mock_llm_client():
    """Mocks the LLM client."""
    llm = MagicMock()
    # The LLM is the last step in the chain, so we mock its final output.
    llm.invoke.return_value = "This is the generated answer from the LLM."
    return llm

def test_rag_service_initialization(mock_retriever, mock_llm_client):
    """Tests that the RAGService initializes correctly."""
    service = RAGService(retriever=mock_retriever, llm_client=mock_llm_client)
    assert service.retriever is mock_retriever
    assert service.rag_chain is not None, "The LangChain runnable should be created."

def test_rag_service_ask_with_documents(mock_retriever, mock_llm_client):
    """Tests the ask method when documents are successfully retrieved."""
    # Arrange
    mock_docs = [
        Document(page_content="Content from doc 1.", metadata={"source": "doc1.pdf"}),
        Document(page_content="Content from doc 2.", metadata={"source": "doc2.pdf"}),
    ]
    mock_retriever.retrieve.return_value = mock_docs
    
    # To test the service's orchestration, we can mock the chain it builds.
    rag_chain_mock = MagicMock()
    rag_chain_mock.invoke.return_value = "This is the generated answer."

    service = RAGService(retriever=mock_retriever, llm_client=mock_llm_client)
    service.rag_chain = rag_chain_mock # Override the real chain with a mock for this test
    
    # Act
    result = service.ask("What is the policy?")
    
    # Assert
    mock_retriever.retrieve.assert_called_once_with(query="What is the policy?", k=5)
    expected_context = "Content from doc 1.\n\n---\n\nContent from doc 2."
    rag_chain_mock.invoke.assert_called_once_with({"context": expected_context, "question": "What is the policy?"})
    
    assert isinstance(result, RAGResult)
    assert result.text == "This is the generated answer."
    assert result.sources == ["doc1.pdf", "doc2.pdf"]

def test_rag_service_ask_no_documents(mock_retriever, mock_llm_client):
    """Tests the ask method when no documents are retrieved."""
    # Arrange
    mock_retriever.retrieve.return_value = [] # Simulate no documents found
    service = RAGService(retriever=mock_retriever, llm_client=mock_llm_client)
    
    # Act
    result = service.ask("What about an obscure topic?")
    
    # Assert
    mock_retriever.retrieve.assert_called_once_with(query="What about an obscure topic?", k=5)
    assert isinstance(result, RAGResult)
    assert result.text == "I could not find relevant information in the documents to answer your question."
    assert result.sources == []