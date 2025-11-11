import os
from typing import List, Tuple
from langchain_core.documents import Document
from ..tools.semantic_search import search_docs


def retrieve_context(
    objective: str,
    collection_name: str = "docs",
    k: int = 5,
    max_distance: float = None,
) -> str:
    """
    Retrieve concatenated context for an objective from the vector store,
    filtering by a distance threshold (lower is better). Logs useful details.
    """
    if not objective:
        return ""
    try:
        threshold = max_distance
        if threshold is None:
            try:
                threshold = float(os.getenv("RAG_MAX_DISTANCE", "0.35"))
            except Exception:
                threshold = 0.35
        print(f"[RAG] Using collection={collection_name!r}, k={k}, max_distance={threshold}")
        results: List[Tuple[Document, float]] = search_docs(objective, collection_name=collection_name, k=k)
        filtered: List[Tuple[Document, float]] = [
            (doc, dist) for doc, dist in results if dist is not None and dist <= threshold
        ]
        if not filtered:
            print(f"[RAG] No chunks under distance threshold {threshold}.")
            return ""
        print(f"[RAG] Found {len(filtered)} chunk(s) within distance <= {threshold}.")
        top, top_dist = filtered[0]
        try:
            src = (top.metadata or {}).get("source")
        except Exception:
            src = None
        if src:
            print(f"[RAG] Top chunk source: {src}")
        print(f"[RAG] Top chunk distance: {top_dist}")
        preview = top.page_content[:300]
        suffix = "..." if len(top.page_content) > 300 else ""
        print(f"[RAG] Top chunk preview:\n{preview}{suffix}")
        context = "\n\n".join([doc.page_content for doc, dist in filtered])
        return context
    except Exception as e:
        print(f"[RAG] Error in retrieve_context: {e}")
        return ""


