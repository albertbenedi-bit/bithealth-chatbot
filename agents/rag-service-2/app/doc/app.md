app/main.py

Purpose: To initialize and configure the FastAPI application, manage its lifecycle, and integrate all the necessary components like API routes and middleware.
Key Components:
FastAPI(lifespan=lifespan): Creates the main application instance. The lifespan argument is crucial; it points to an asynccontextmanager function that controls startup and shutdown logic.
lifespan(app: FastAPI): This async context manager is responsible for initializing the KafkaClient and the KafkaMessageHandler when the service starts. It creates a background task to consume Kafka messages. During shutdown, it gracefully stops the Kafka client and cancels the background task. This is the modern and recommended way to handle background tasks and resource management in FastAPI.
app.include_router(endpoints.router): This line incorporates all the API routes defined in app/api/v1/endpoints.py, making them accessible.
Middleware: It includes CORSMiddleware to handle Cross-Origin Resource Sharing, allowing front-end applications from different domains to interact with the API.
Logging: Basic logging is configured to write to a rag_service.log file, which is essential for debugging and monitoring in a production environment.


app/api/v1/endpoints.py
This file defines the RESTful API endpoints for the service.

Purpose: To provide a synchronous, HTTP-based interface for interacting with the RAG service.
Key Components:
router = APIRouter(...): Creates a FastAPI router, which helps in organizing endpoints, especially for versioning (e.g., /v1).
@router.post("/ask"): Defines the primary endpoint for asking questions. It uses FastAPI's dependency injection (Depends(...)) to get instances of the PGVectorRetriever and the LLM client. It orchestrates the RAG pipeline: retrieve documents, format context, invoke the LLM, and return a structured Answer.
@router.get("/health"): Defines a health check endpoint. This is critical for monitoring and for container orchestration systems like Kubernetes to determine if the service is alive and ready to serve traffic. It checks the status of its dependencies, including Kafka.
python
 Show full code block 
# c:\Users\Tan Prawibowo\BTH_AWS_TF\pv_chatbot_general\agents\rag-service-2\app\api\v1\endpoints.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session # Import Session for DB dependency type hint
from typing import List, Dict, Any

# Import your dependencies
from app.core.dependencies import (
    get_db, # Although get_db is used by get_retriever internally,
            # you might want it here for a direct DB health check
    get_llm_client,
    get_retriever, # This now provides the PGVectorRetriever instance
    get_embedding_model # You might not need this directly in the endpoint anymore
)
from app.core.llm import load_llm_client # Used for health check instantiation
from app.core.retriever import PGVectorRetriever # Import the Retriever class

# Import models (define these in app/models/rag.py)
from app.models.rag import Question, Answer # Assuming you create app/models/rag.py

# Langchain imports for the RAG chain
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document # Import Document type hint


router = APIRouter(prefix="/v1", tags=["rag"]) # Use v1 prefix for versioning

# --- /ask Endpoint ---
@router.post("/ask", response_model=Answer) # Specify the response model for docs and validation
def ask_question(
    question: Question, # Expect a JSON body matching the Question Pydantic model
    # Inject the configured dependencies
    # db: Session = Depends(get_db), # Inject DB session if needed directly for query/logging
    retriever: PGVectorRetriever = Depends(get_retriever), # Inject our custom retriever
    llm_client = Depends(get_llm_client) # Inject the LLM client instance
):
    """
    Receives a user query, performs RAG to find relevant information,
    and returns an AI-generated answer based on internal documents.
    """
    print(f"Received question: {question.text}")

    # Perform basic checks that dependencies were initialized
    if llm_client is None or retriever is None:
         # This should ideally be caught during service startup if dependencies.py
         # fails fatally, but an extra check is good.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG service dependencies are not initialized."
        )

    try:
        # --- RAG Execution ---

        # 1. Retrieve relevant documents using the injected retriever
        # Use parameters from settings or hardcode defaults for now
        retrieved_docs: List[Document] = retriever.retrieve(
            query=question.text,
            k=5, # Example: retrieve top 5 documents
            search_type="similarity" # Example: use similarity search
        )

        if not retrieved_docs:
            # Handle cases where no relevant documents are found
            print("No relevant documents found for the query.")
            # You might return a specific message or trigger handover logic here
            # For the RAG service, we'll just return a canned response or empty answer
            return Answer(
                text="I could not find relevant information in the documents to answer your question.",
                sources=[]
            )


        # 2. Format the retrieved documents into context for the LLM
        context_text = "\n\n---\n\n".join([doc.page_content for doc in retrieved_docs])
        print(f"Context sent to LLM:\n{context_text[:200]}...") # Print snippet of context

        # 3. Define the LLM Prompt (using Langchain's ChatPromptTemplate)
        # Incorporate prompt engineering techniques (System, Contextual, etc. from PDF)
        prompt_template = """
        You are an AI assistant specialized in answering questions based on the provided context.
        Answer the user's question truthfully and concisely, using ONLY the information from the following documents.
        If the documents do not contain the answer, state that you cannot find the answer in the provided information.
        Do NOT make up information.
        Cite the source document(s) (if metadata is available) for your answer.

        Context:
        {context}

        Question:
        {question}

        Answer:
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)

        # 4. Build and Invoke the RAG Chain (using Langchain Runnable)
        rag_chain = (
            {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
            | prompt
            | llm_client # Use the injected LLM client
            | StrOutputParser()
        )

        print("Invoking RAG chain...")
        # Invoke the chain with the formatted context and original question
        answer_text = rag_chain.invoke({"context": context_text, "question": question.text})
        print("RAG chain completed.")

        # 5. Extract Source Metadata
        source_metadata = [doc.metadata.get('source', 'N/A') for doc in retrieved_docs]
        # Remove duplicates while preserving order (or sort them)
        unique_sources = list(dict.fromkeys(source_metadata))


        # 6. Return the structured response
        return Answer(
            text=answer_text,
            sources=unique_sources
        )

    except Exception as e:
        # --- Error Handling ---
        # Log the error for debugging
        print(f"An error occurred during RAG processing: {e}")
        # In production, log full traceback
        # import traceback
        # print(traceback.format_exc())

        # Return a generic error response to the client
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing your request."
        )

# --- /health Endpoint ---
@router.get("/health")
async def health_check(
    db_check: Session = Depends(get_db), # Checks if DB session can be established
    llm_check = Depends(get_llm_client), # Checks if LLM client instance is available
    retriever_check: PGVectorRetriever = Depends(get_retriever)
):
    """
    Checks the health of the RAG service and its primary dependencies, including Kafka.
    """
    # --- Kafka Health Check ---
    kafka_status = "unknown"
    kafka_error = None

    async def check_kafka():
        nonlocal kafka_status, kafka_error
        try:
            from app.messaging.kafka_client import KafkaClient
            from app.core.config import settings
            kafka_client = KafkaClient()
            # Only check connection, do not start consuming
            kafka_client.producer = None
            kafka_client.consumer = None
            # Try to initialize producer and consumer
            try:
                kafka_client.producer = kafka_client.producer or kafka_client.producer
                kafka_client.consumer = kafka_client.consumer or kafka_client.consumer
                # Actually try to connect
                await kafka_client.start()
                kafka_status = "ok"
            except Exception as e:
                kafka_status = "error"
                kafka_error = str(e)
            finally:
                await kafka_client.stop()
        except Exception as e:
            kafka_status = "error"
            kafka_error = str(e)

    await check_kafka()

    health = {
        "status": "ok" if kafka_status == "ok" else "degraded",
        "message": "RAG service is healthy." if kafka_status == "ok" else "RAG service is running, but Kafka connection failed.",
        "kafka_status": kafka_status,
        "kafka_error": kafka_error
    }
    return health
app/handlers/kafka_handler.py
This file contains the core logic for the asynchronous, message-driven functionality of the service.

Purpose: To process RAG requests that arrive via Kafka topics, decoupling the service from synchronous HTTP requests.
Key Components:
KafkaMessageHandler: A class that encapsulates the logic for handling incoming messages.
initialize_dependencies(): This async method is critical. Since the handler operates outside the FastAPI request-response cycle, it cannot use Depends. Instead, it manually initializes the dependencies it needs (the PGVectorRetriever and the LLM client) when the service starts up. This ensures it's ready to process messages as soon as they arrive.
handle_message(): The callback function that is executed for each message consumed from Kafka. It parses the message, validates it against a Pydantic model (TaskRequest), and then calls the appropriate handler (e.g., _handle_general_info_request).
_handle_general_info_request(): This method contains the RAG business logic, which is nearly identical to the /ask endpoint. It retrieves documents, generates an answer, and then uses the kafka_client to send a TaskResponse message to a response topic.

app/models/document_chunks.py
This file defines the data model for the documents stored in the database.

Purpose: To create a SQLAlchemy ORM (Object-Relational Mapping) model that represents the document_chunks table in the PostgreSQL database.
Key Components:
DocumentChunk(Base): The Python class that maps to the database table.
__tablename__: Specifies the name of the table in the database.
Column(...): Defines the table's columns:
content: The raw text of the document chunk.
embedding: The vector representation of the content. The Vector(384) type is provided by the pgvector library and is crucial for enabling vector similarity searches. The dimension (384) must match the output dimension of the embedding model being used.
source: Metadata to track the origin of the document chunk (e.g., the filename).