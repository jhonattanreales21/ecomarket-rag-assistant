"""RAG pipeline: builds and persists the FAISS vectorstore.

This module handles:
- Chunking documents with RecursiveCharacterTextSplitter
- Generating embeddings via HuggingFace sentence-transformers
- Creating or loading a FAISS index from disk

The vectorstore is saved to vectorstore/faiss_index/ so it is only
built once and reloaded on subsequent runs.
"""

from pathlib import Path
from typing import List

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from src.document_loader import load_all_documents

# ── configuration ────────────────────────────────────────────────────────────

VECTORSTORE_DIR = Path("vectorstore/faiss_index")

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Chunking strategy — justified by EDA in docs/eda_chunking_analysis.md
CHUNK_SIZE = 700
CHUNK_OVERLAP = 100

# ── embedding model (singleton) ───────────────────────────────────────────────


def get_embeddings() -> HuggingFaceEmbeddings:
    """Return a HuggingFace embeddings instance.

    Uses all-MiniLM-L6-v2 which is fast, lightweight, and performs well
    on English semantic similarity tasks.
    """
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


# ── chunking ─────────────────────────────────────────────────────────────────


def chunk_documents(documents: List[Document]) -> List[Document]:
    """Split documents into overlapping chunks.

    Args:
        documents: Raw Documents from the document loader.

    Returns:
        Chunked Documents with inherited metadata.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    print(
        f"[rag_pipeline] Produced {len(chunks)} chunks from {len(documents)} documents."
    )
    return chunks


# ── vectorstore build / load ──────────────────────────────────────────────────


def build_vectorstore(
    chunks: List[Document], embeddings: HuggingFaceEmbeddings
) -> FAISS:
    """Build a FAISS vectorstore from the given chunks and save it to disk.

    Args:
        chunks: Chunked Documents to index.
        embeddings: Embedding model instance.

    Returns:
        Populated FAISS vectorstore.
    """
    print(f"[rag_pipeline] Building vectorstore with {len(chunks)} chunks…")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(VECTORSTORE_DIR))
    print(f"[rag_pipeline] Vectorstore saved to {VECTORSTORE_DIR}.")
    return vectorstore


def load_vectorstore(embeddings: HuggingFaceEmbeddings) -> FAISS:
    """Load an existing FAISS vectorstore from disk.

    Args:
        embeddings: Must be the same model used during build.

    Returns:
        Loaded FAISS vectorstore.
    """
    print(f"[rag_pipeline] Loading vectorstore from {VECTORSTORE_DIR}.")
    return FAISS.load_local(
        str(VECTORSTORE_DIR),
        embeddings,
        allow_dangerous_deserialization=True,
    )


def get_vectorstore(force_rebuild: bool = False) -> FAISS:
    """Return a ready-to-use FAISS vectorstore, building it if necessary.

    If the index already exists on disk and ``force_rebuild`` is False, the
    saved index is loaded directly to avoid re-embedding on every startup.

    Args:
        force_rebuild: When True, always rebuild from source documents.

    Returns:
        FAISS vectorstore instance.

    Raises:
        RuntimeError: If documents cannot be loaded.
    """
    embeddings = get_embeddings()
    index_file = VECTORSTORE_DIR / "index.faiss"

    if not force_rebuild and index_file.exists():
        return load_vectorstore(embeddings)

    documents = load_all_documents()
    if not documents:
        raise RuntimeError(
            "[rag_pipeline] No documents were loaded. "
            "Check that data files exist in the data/ directory."
        )

    chunks = chunk_documents(documents)
    return build_vectorstore(chunks, embeddings)
