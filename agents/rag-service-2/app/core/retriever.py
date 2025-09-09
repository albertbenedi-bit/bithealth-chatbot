# rag-service/app/core/retriever.py

from langchain_community.vectorstores.pgvector import PGVector
from langchain_core.documents import Document # To type hint returned documents
from typing import List

class PGVectorRetriever:
    """
    Encapsulates logic for performing vector searches against a PGVector store.
    """
    def __init__(self, pgvector_store: PGVector):
        """
        Initializes the retriever with a configured PGVector store instance.

        Args:
            pgvector_store: An initialized instance of Langchain's PGVector.
        """
        if not isinstance(pgvector_store, PGVector):
             raise TypeError("pgvector_store must be an instance of langchain_community.vectorstores.pgvector.PGVector")
        self._vector_store = pgvector_store
        print("PGVectorRetriever initialized.")

    def retrieve(self, query: str, k: int = 4, search_type: str = "similarity") -> List[Document]:
        """
        Performs a vector search against the PGVector store to find relevant documents.

        Args:
            query: The user's query string.
            k: The number of top similar documents to retrieve.
            search_type: The type of search ("similarity" or "mmr").

        Returns:
            A list of Langchain Document objects representing the retrieved chunks.

        Raises:
            Exception: If an error occurs during the retrieval process.
        """
        print(f"Performing '{search_type}' search for query: '{query[:50]}...' with k={k}")
        try:
            # Use the underlying Langchain PGVector instance to perform the search
            if search_type == "similarity":
                # Langchain's similarity_search handles embedding the query internally
                retrieved_docs = self._vector_store.similarity_search(query, k=k)
            elif search_type == "mmr":
                # Langchain's max_marginal_relevance_search handles MMR
                retrieved_docs = self._vector_store.max_marginal_relevance_search(query, k=k)
            else:
                raise ValueError(f"Unsupported search type: {search_type}")

            print(f"Retrieved {len(retrieved_docs)} documents.")
            return retrieved_docs

        except Exception as e:
            print(f"Error during vector retrieval: {e}")
            # Log the full exception traceback in production
            raise # Re-raise the exception


# --- How this would be used in dependencies.py ---
# In app/core/dependencies.py, instead of defining get_vector_store_retriever
# that returns the Langchain Retriever object directly, you could define one
# that returns an instance of this PGVectorRetriever class:

# from .retriever import PGVectorRetriever # Import the class

# def get_retriever(
#     pgvector_store_instance: PGVector = Depends(get_pgvector_store_instance) # Assuming a dependency that provides the PGVector instance
# ) -> PGVectorRetriever:
#     """
#     Dependency that provides a configured PGVectorRetriever instance.
#     """
#     # Create an instance of our custom retriever class
#     return PGVectorRetriever(pgvector_store=pgvector_store_instance)

# Note: You might need to adjust your dependencies.py to provide the raw PGVector
# instance if you use this custom class, or initialize PGVector directly within
# the get_retriever dependency function, depending on where you want to manage
# the PGVector lifecycle and configuration (embeddings, connection).
# The previous dependencies.py example directly created the Langchain Retriever,
# which is a simpler approach if you don't need the extra abstraction of this class.
# Choose one approach (Langchain's retriever or your custom class wrapping it)
# and stick with it for consistency. The custom class offers more flexibility for
# adding complex retrieval logic later.