# rag-service/app/core/embeddings.py

from sentence_transformers import SentenceTransformer # Import directly from the library
# from langchain_community.embeddings import SentenceTransformerEmbeddings # Alternative using Langchain wrapper
from .config import settings # Import application settings

# While you could instantiate the model directly here:
# embedding_model_instance = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
# It's often better to have a function that does it,
# giving more control to the caller (like dependencies.py)

def load_sentence_transformer_model(model_name: str) -> SentenceTransformer:
    """
    Loads a SentenceTransformer model.

    Args:
        model_name: The name of the SentenceTransformer model to load (e.g., "all-MiniLM-L6-v2").

    Returns:
        An instance of the loaded SentenceTransformer model.

    Raises:
        Exception: If the model fails to load.
    """
    print(f"Loading SentenceTransformer model: {model_name}")
    try:
        # Instantiate the model. This might download weights if not cached.
        model = SentenceTransformer(model_name)
        print(f"Successfully loaded SentenceTransformer model: {model_name}")
        return model
    except Exception as e:
        print(f"Error loading SentenceTransformer model '{model_name}': {e}")
        # Re-raise the exception or return None, depending on desired error handling
        raise # Re-raise to signal failure during initialization


# Note: If you were using Langchain's wrapper directly for consistency with PGVector,
# the function might look like this:
# def load_langchain_sentence_transformer_wrapper(model_name: str) -> SentenceTransformerEmbeddings:
#      print(f"Loading Langchain SentenceTransformer wrapper for model: {model_name}")
#      try:
#          # Instantiate the Langchain wrapper
#          wrapper = SentenceTransformerEmbeddings(model_name=model_name)
#          print(f"Successfully loaded Langchain wrapper for model: {model_name}")
#          return wrapper
#      except Exception as e:
#          print(f"Error loading Langchain wrapper for model '{model_name}': {e}")
#          raise # Re-raise


# In your dependencies.py, you would then call this function:
# from .embeddings import load_sentence_transformer_model
# embedding_model_instance = load_sentence_transformer_model(settings.EMBEDDING_MODEL_NAME)