# rag-service/app/core/llm.py

# Import necessary Langchain LLM components
from langchain_community.llms import Ollama # For local Ollama models
from langchain_google_genai import ChatGoogleGenerativeAI # For Google Gemini models
# Add other LLM imports as needed (e.g., from langchain_openai import ChatOpenAI)


from .config import settings # Import application settings
# from . import exceptions # You might define custom exceptions

def load_llm_client(model_name: str, google_api_key: str | None = None):
    """
    Loads and initializes the appropriate LLM client based on the model name.

    Args:
        model_name: The name of the LLM model (e.g., "llama2", "gemini-2.5-flash","gemini-pro", "gpt-4o").
        google_api_key: Optional API key for Google models.

    Returns:
        An instance of the loaded LLM client (e.g., Ollama, ChatGoogleGenerativeAI).

    Raises:
        ValueError: If the model name is unsupported or configuration is missing.
        Exception: If the LLM client fails to initialize.
    """
    print(f"Attempting to load LLM client for model: {model_name}")

    try:
        # --- Logic to choose and initialize the correct LLM client ---

        # Example: Ollama
        if model_name.lower() in ["llama2", "mistral", "phi3"]: # Add other local Ollama models
            print(f"Initializing Ollama client for model: {model_name}")
            # Ensure Ollama server is running and model is pulled
            llm_client = Ollama(model=model_name)
            print(f"Ollama client initialized for model: {model_name}")
            return llm_client

        # Example: Google Generative AI (Gemini models)
        elif model_name.startswith("gemini"):
            if not google_api_key:
                 raise ValueError(f"Google API key is required for model: {model_name}")
            print(f"Initializing Google Generative AI client for model: {model_name}")
            llm_client = ChatGoogleGenerativeAI(model=model_name, google_api_key=google_api_key)
            print(f"Google Generative AI client initialized for model: {model_name}")
            return llm_client

        # Example: OpenAI (if you add support later)
        # elif model_name.startswith("gpt"):
        #     from langchain_openai import ChatOpenAI
        #     openai_api_key = settings.OPENAI_API_KEY # Assuming you add this to settings
        #     if not openai_api_key:
        #          raise ValueError(f"OpenAI API key is required for model: {model_name}")
        #     print(f"Initializing OpenAI client for model: {model_name}")
        #     llm_client = ChatOpenAI(model=model_name, api_key=openai_api_key)
        #     print(f"OpenAI client initialized for model: {model_name}")
        #     return llm_client

        # --- Handle Unsupported Models ---
        else:
            raise ValueError(f"Unsupported LLM model name specified: {model_name}")

    except ValueError as ve:
        print(f"Configuration error loading LLM model '{model_name}': {ve}")
        raise # Re-raise the configuration error

    except Exception as e:
        print(f"Unexpected error loading LLM client for model '{model_name}': {e}")
        # Re-raise any other exceptions during initialization
        raise


# In your dependencies.py, you would then call this function during singleton initialization:
# from .llm import load_llm_client
# llm_client_instance = load_llm_client(settings.LLM_MODEL_NAME, settings.GOOGLE_API_KEY) # Pass required params