import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from ..config import get_google_api_key


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """
    Returns Gemini (Google) embeddings instance.
    Reads API key from GOOGLE_API_KEY.
    """
    # Default Gemini embeddings model; override with GOOGLE_EMBEDDINGS_MODEL if needed
    # Google API expects the "models/..." prefix
    model = os.getenv("GOOGLE_EMBEDDINGS_MODEL", "models/text-embedding-004")
    if not model.startswith("models/"):
        model = f"models/{model}"
    api_key = get_google_api_key()
    return GoogleGenerativeAIEmbeddings(model=model, google_api_key=api_key)


