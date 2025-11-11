import os
from typing import Optional
from langchain_postgres import PGVector
from .embeddings import get_embeddings


def get_vector_store(collection_name: str = "docker_docs") -> Optional[PGVector]:
    """
    Returns a PGVector store using VECTOR_DB_URL (psycopg driver).
    If VECTOR_DB_URL is not set, returns None.
    """
    connection = os.getenv("VECTOR_DB_URL")
    if not connection:
        return None
    # Normalize SQLAlchemy URL to include driver if missing
    # Accept both postgresql:// and postgresql+psycopg://
    if connection.startswith("postgresql://"):
        connection = connection.replace("postgresql://", "postgresql+psycopg://", 1)
    embeddings = get_embeddings()
    return PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=connection,
    )


