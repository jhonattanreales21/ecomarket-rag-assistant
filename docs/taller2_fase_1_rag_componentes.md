# Phase 1: RAG Components — Embedding Model and Vector Store

## Overview

This document covers the core infrastructure choices for the EcoMarket RAG system:
the embedding model and the vector database. These decisions directly affect
retrieval quality, cost, deployment complexity, and scalability.

---

## 1. Embedding Model

### Selected model: `sentence-transformers/all-MiniLM-L6-v2`

| Property | Value |
|---|---|
| Library | `sentence-transformers` via `langchain-huggingface` |
| Model size | ~22 MB |
| Max input tokens | 512 |
| Embedding dimension | 384 |
| Device | CPU (no GPU required) |
| Normalization | L2 normalized (cosine similarity via dot product) |

### Why this model?

1. **Lightweight and fast**: At 22 MB, it loads in seconds and runs on any machine
   without a GPU. This is essential for a local academic prototype.

2. **Strong English semantic similarity**: `all-MiniLM-L6-v2` was specifically trained
   on a diverse English dataset for semantic textual similarity. It outperforms
   bag-of-words approaches (BM25, TF-IDF) on conversational and question-answering tasks.

3. **No API cost**: Unlike OpenAI Embeddings (ada-002) or Cohere, this model runs
   entirely locally — there are no per-query costs or API rate limits.

4. **LangChain integration**: `HuggingFaceEmbeddings` provides a drop-in wrapper
   that is fully compatible with FAISS, ChromaDB, and other LangChain-supported stores.

5. **Reproducibility**: Since the model weights are fixed and downloaded once,
   embeddings are deterministic and reproducible across runs.

### Spanish language considerations

The current corpus (PDFs, Excel, JSON) is written in English. `all-MiniLM-L6-v2` is
trained primarily on English data and performs well for this use case.

If the project moves to Spanish-language documents in a future phase, the recommended
upgrade is:

- `intfloat/multilingual-e5-base` — multilingual, supports Spanish and English
- `paraphrase-multilingual-MiniLM-L12-v2` — multilingual variant of MiniLM

For the current MVP, English embeddings are appropriate and sufficient.

---

## 2. Vector Store

### Selected store: FAISS (Facebook AI Similarity Search)

| Property | Value |
|---|---|
| Library | `faiss-cpu` via `langchain-community` |
| Storage | Local disk (`vectorstore/faiss_index/`) |
| Index type | Flat L2 (exact search) |
| Persistence | `save_local` / `load_local` |
| Filtering | Supported via metadata filters |

### Why FAISS?

1. **Local and free**: FAISS runs entirely in-process with no external service.
   Ideal for academic projects, local development, and offline demos.

2. **Fast for small corpora**: Our corpus is ~500–700 chunks. FAISS performs exact
   nearest-neighbor search in milliseconds at this scale.

3. **No infrastructure required**: Unlike managed vector databases, FAISS requires
   no Docker container, cloud subscription, or API key.

4. **LangChain native support**: `FAISS.from_documents()`, `save_local()`, and
   `load_local()` are first-class LangChain primitives, simplifying integration.

5. **Disk persistence**: The index is saved after the first build and reloaded on
   subsequent runs — avoiding expensive re-embedding every startup.

---

## 3. Comparison with Alternative Vector Stores

| Store | Type | Cost | Setup Complexity | Scalability | Best For |
|---|---|---|---|---|---|
| **FAISS** | Local library | Free | Low | Medium (~1M vectors) | Local dev, academic projects |
| ChromaDB | Local/cloud | Free (local) | Low | Medium | Dev, embedded use |
| Pinecone | Managed cloud | Paid | Low | Very high | Production SaaS |
| Weaviate | Self-hosted/cloud | Free (OSS) | High | Very high | Enterprise, multi-modal |
| Qdrant | Self-hosted/cloud | Free (OSS) | Medium | High | Production, filtering |
| pgvector | PostgreSQL ext. | Free | Medium | High | Existing Postgres users |

### FAISS vs ChromaDB

ChromaDB is the closest alternative to FAISS for local use. Both are free and
easy to set up. The key differences:

- ChromaDB offers a more developer-friendly API with built-in persistence via SQLite.
- FAISS is faster for pure similarity search but requires manual save/load.
- ChromaDB supports metadata filtering natively; FAISS filtering requires extra steps
  (LangChain wraps this transparently).
- For this project, both would work equally well. FAISS was chosen for its maturity,
  widespread use in LangChain tutorials, and minimal dependencies.

### FAISS vs Pinecone

Pinecone is a fully managed vector database optimized for production scale:
- Pinecone requires an API key and charges per query above the free tier.
- It supports real-time upserts, which FAISS does not (FAISS requires rebuilding the index).
- For a local academic MVP, Pinecone adds unnecessary complexity and cost.
- If EcoMarket were a real production system with millions of documents, Pinecone
  would be a strong candidate.

### FAISS vs Weaviate

Weaviate is a full-featured vector search engine:
- It runs as a Docker service and supports multi-tenancy, filtering, and GraphQL queries.
- It offers much more power than needed for this project.
- Recommended only if the team needs hybrid search (keyword + semantic) or complex
  metadata filtering at scale.

---

## 4. Embedding Pipeline Configuration

```python
from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)
```

Setting `normalize_embeddings=True` ensures that cosine similarity can be computed
via simple dot product, which is what FAISS's flat L2 index uses internally.

---

## 5. Summary

| Decision | Choice | Reason |
|---|---|---|
| Embedding model | `all-MiniLM-L6-v2` | Fast, free, strong English semantic similarity |
| Vector store | FAISS (faiss-cpu) | Local, free, LangChain-native, persistent |
| Device | CPU | No GPU required, compatible with any machine |
| Normalization | L2 normalized | Enables cosine similarity via dot product |
| Persistence | Local disk | Avoids re-embedding on every app restart |
