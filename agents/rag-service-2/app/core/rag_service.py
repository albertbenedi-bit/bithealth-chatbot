# rag-service-2/app/core/rag_service.py

from typing import List
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, Runnable
from langchain_core.documents import Document
from app.core.retriever import PGVectorRetriever
from app.models.rag import RAGResult

# Type hinting for the LLM client
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.llms import Ollama

class RAGService:
    """
    Encapsulates the core Retrieval Augmented Generation (RAG) logic.
    This service is responsible for taking a question, retrieving relevant context
    from a vector store, and generating a fact-based answer using an LLM.
    """

    _prompt_template = """
    You are an AI assistant specialized in answering questions based on the provided context.
    Answer the user's question truthfully and concisely, using ONLY the information from the following documents.
    If the documents do not contain the answer, state that you cannot find the answer in the provided information.
    Do NOT make up information.

    Context:
    {context}

    Question:
    {question}

    Answer:
    """

    def __init__(self, retriever: PGVectorRetriever, llm_client: Ollama | ChatGoogleGenerativeAI):
        if not retriever or not llm_client:
            raise ValueError("Retriever and LLM client must be provided.")
        self.retriever = retriever
        
        prompt = ChatPromptTemplate.from_template(self._prompt_template)
        
        # Define the LangChain Runnable chain
        self.rag_chain: Runnable = (
            {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
            | prompt
            | llm_client
            | StrOutputParser()
        )

    def ask(self, question: str, k: int = 5) -> RAGResult:
        retrieved_docs: List[Document] = self.retriever.retrieve(query=question, k=k)

        if not retrieved_docs:
            return RAGResult(text="I could not find relevant information in the documents to answer your question.", sources=[])

        context_text = "\n\n---\n\n".join([doc.page_content for doc in retrieved_docs])
        answer_text = self.rag_chain.invoke({"context": context_text, "question": question})
        unique_sources = list(dict.fromkeys([doc.metadata.get('source', 'N/A') for doc in retrieved_docs]))

        return RAGResult(text=answer_text, sources=unique_sources)