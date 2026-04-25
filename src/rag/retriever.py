"""Retriever module: wraps the FAISS vectorstore for similarity search.

Provides a simple interface to retrieve the top-k most relevant
document chunks for a user query, along with their source metadata.
"""

from typing import List, Tuple

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

DEFAULT_K = 4


def retrieve(
    query: str,
    vectorstore: FAISS,
    k: int = DEFAULT_K,
    filter_doc_type: str | None = None,
) -> List[Tuple[Document, float]]:
    """Retrieve the top-k relevant chunks for a query.

    Args:
        query: The user's natural-language question.
        vectorstore: Loaded FAISS vectorstore.
        k: Number of chunks to retrieve.
        filter_doc_type: Optional doc_type value to restrict retrieval.
            Example values: 'returns_policy', 'shipping_policy',
            'inventory', 'product_catalog', 'order', 'support_example'.

    Returns:
        List of (Document, score) tuples sorted by relevance (lower score
        means closer in embedding space).
    """
    if filter_doc_type:
        results = vectorstore.similarity_search_with_score(
            query,
            k=k,
            filter={"doc_type": filter_doc_type},
        )
    else:
        results = vectorstore.similarity_search_with_score(query, k=k)

    return results


def retrieve_context_text(
    query: str,
    vectorstore: FAISS,
    k: int = DEFAULT_K,
    filter_doc_type: str | None = None,
) -> Tuple[str, List[dict]]:
    """Return retrieved context as a single formatted string and a metadata list.

    Args:
        query: The user's question.
        vectorstore: Loaded FAISS vectorstore.
        k: Number of chunks to retrieve.
        filter_doc_type: Optional filter by document type.

    Returns:
        Tuple of:
          - context_text: Concatenated chunk texts separated by markers.
          - sources: List of metadata dicts for display in the UI.
    """
    results = retrieve(query, vectorstore, k=k, filter_doc_type=filter_doc_type)

    context_parts: List[str] = []
    sources: List[dict] = []

    for doc, score in results:
        context_parts.append(doc.page_content)
        sources.append(
            {
                "doc_type": doc.metadata.get("doc_type", "unknown"),
                "source": doc.metadata.get("source", "unknown"),
                "score": round(float(score), 4),
                **{
                    k: v
                    for k, v in doc.metadata.items()
                    if k not in ("doc_type", "source")
                },
            }
        )

    context_text = "\n\n---\n\n".join(context_parts)
    return context_text, sources
