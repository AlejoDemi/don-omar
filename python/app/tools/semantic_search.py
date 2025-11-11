from typing import List, Tuple
from langchain_core.documents import Document
from .db_vector_store import get_vector_store


def search_docs(query: str, collection_name: str = "docs", k: int = 1) -> List[Tuple[Document, float]]:
    """
    Performs semantic similarity search returning (Document, distance) pairs.
    Lower distance == more similar.
    """
    vector_store = get_vector_store(collection_name=collection_name)
    if vector_store is None:
        return []
    return vector_store.similarity_search_with_score(query, k=k)


