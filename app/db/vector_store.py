from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from app.core.config import settings


def create_vector_store(chunks, user_id):
    """
    Creates a Chroma vector store for a given user's resume chunks.
    """
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=settings.GEMINI_API_KEY
    )

    metadatas = [{"user_id": user_id}] * len(chunks)

    db = Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        metadatas=metadatas,
        persist_directory=settings.CHROMA_DB_DIR
    )

    return db
