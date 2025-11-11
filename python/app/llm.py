from typing import Optional
from .config import get_google_model_name, get_google_api_key


def build_chat_llm():
    """
    Returns a LangChain chat model instance or None if not available/misconfigured.
    """
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except Exception:
        return None

    api_key = get_google_api_key()
    if not api_key:
        return None

    model = get_google_model_name()
    try:
        return ChatGoogleGenerativeAI(model=model, api_key=api_key, temperature=0.2)
    except Exception:
        return None


