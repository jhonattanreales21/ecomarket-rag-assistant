# Phase 3: Code Integration — End-to-End RAG Pipeline

## Overview

This document explains how the EcoMarket RAG system works end-to-end:
from user input to generated response. It covers each module, the data flow
between components, prompt construction, and how Streamlit ties everything together.

---

## 1. System Architecture

```
User input (Streamlit chat)
        │
        ▼
  detect_intent()  [src/core/router.py]
        │
        ├── order_status
        │       ├── extract_tracking_number()  [src/core/utils.py]
        │       ├── get_order()  [src/services/order_service.py]  ← structured truth
        │       ├── retrieve_context_text()  [src/rag/retriever.py]  ← RAG enrichment
        │       └── build_order_prompt()  [src/llm/prompts.py]
        │
        ├── return_policy
        │       ├── retrieve_context_text(filter="returns_policy")
        │       └── build_return_prompt()
        │
        ├── shipping
        │       ├── retrieve_context_text(filter="shipping_policy")
        │       └── build_shipping_prompt()
        │
        ├── inventory
        │       ├── extract_product_id()  [src/core/utils.py]
        │       ├── get_product_by_id() / get_products_by_name()  [src/services/inventory_service.py]
        │       ├── retrieve_context_text()  ← RAG enrichment
        │       └── build_inventory_prompt()
        │
        ├── product
        │       ├── retrieve_context_text(filter="product_catalog")
        │       └── build_product_prompt()
        │
        ├── human
        │       └── build_human_prompt()
        │
        └── general
                ├── retrieve_context_text()
                └── build_general_prompt()
                        │
                        ▼
              generate_llm_response()  [src/llm/llm_client.py]
                        │
                        ▼
              Formatted response displayed in Streamlit
```

---

## 2. Module-by-Module Explanation

### 2.1 `src/core/router.py` — Intent Classification

```python
def detect_intent(text: str) -> str
```

Classifies the user input into one of seven intents using keyword matching:
`human`, `order_status`, `return_policy`, `shipping`, `inventory`, `product`, `general`.

Keyword matching is simple, fast, and transparent. It avoids the latency of
asking the LLM to classify intent before generating a response. The priority
order ensures that escalation (`human`) always takes precedence.

**Limitation:** Keyword matching can fail on ambiguous queries. A future upgrade
could use a fine-tuned classifier or a fast embedding-based classifier.

---

### 2.2 `src/rag/document_loader.py` — Knowledge Base Loading

Six loader functions convert raw files into LangChain `Document` objects:

| Function | Source |
|---|---|
| `load_returns_policy()` | `returns_policy_extended.pdf` |
| `load_shipping_policy()` | `shipping_policy.pdf` |
| `load_inventory()` | `inventory_200_products_named.xlsx` |
| `load_product_catalog()` | `product_catalog.xlsx` |
| `load_orders_as_docs()` | `orders_enhanced.json` |
| `load_support_examples()` | `support_examples_enhanced.json` |

`load_all_documents()` aggregates all six sources and returns a flat list of Documents.

Each Document has:
- `page_content`: The text to embed
- `metadata`: Source path, doc_type, and domain-specific fields

---

### 2.3 `src/rag/rag_pipeline.py` — Vectorstore Build and Load

```python
def get_vectorstore(force_rebuild: bool = False) -> FAISS
```

On first run:
1. Calls `load_all_documents()`
2. Splits with `RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=100)`
3. Generates embeddings with `HuggingFaceEmbeddings(all-MiniLM-L6-v2)`
4. Builds FAISS index with `FAISS.from_documents()`
5. Saves to `vectorstore/faiss_index/`

On subsequent runs:
1. Detects that `vectorstore/faiss_index/index.faiss` exists
2. Loads directly with `FAISS.load_local()`
3. Skips all embedding computation

The vectorstore is cached at the Streamlit session level with `@st.cache_resource`,
so it is built at most once per server restart.

---

### 2.4 `src/rag/retriever.py` — Similarity Search

```python
def retrieve_context_text(
    query: str,
    vectorstore: FAISS,
    k: int = 4,
    filter_doc_type: str | None = None,
) -> Tuple[str, List[dict]]
```

Runs a FAISS similarity search:
- Returns the top-k chunks sorted by cosine similarity score
- Optionally filters by `doc_type` metadata (e.g., only return policy chunks)
- Returns both the concatenated context text and a list of source metadata dicts

The metadata list powers the "Retrieved sources" expander in the Streamlit sidebar.

**Fallback behavior:** If a filtered search returns no results (e.g., no policy
chunks match the query), the app falls back to an unfiltered search over the full
knowledge base.

---

### 2.5 `src/services/order_service.py` — Structured Order Lookup

```python
def get_order(tracking_number: str) -> dict | None
```

Loads `orders_enhanced.json` and returns the order dict that matches the
tracking number (case-insensitive, punctuation-stripped). Returns `None` if not found.

This is the **primary source of truth for orders** — the LLM is never allowed
to invent or guess order status. The structured order dict is injected directly
into the prompt as authoritative data.

---

### 2.6 `src/services/inventory_service.py` — Structured Inventory Lookup

```python
def get_product_by_id(product_id: str) -> dict | None
def get_products_by_name(name: str) -> list[dict]
def format_product_summary(product: dict) -> str
```

Loads `inventory_200_products_named.xlsx` into a cached pandas DataFrame.
Provides exact lookup by product ID and fuzzy lookup by product name.

Like orders, inventory data is **structured truth** — it is not left to the LLM
to interpret or synthesize. The `format_product_summary` function produces a
Markdown table of key product facts that is appended to the LLM's response.

---

### 2.7 `src/llm/prompts.py` — Prompt Construction

Seven dedicated builders, one per intent:

| Function | Intent |
|---|---|
| `build_order_prompt` | `order_status` |
| `build_return_prompt` | `return_policy` |
| `build_shipping_prompt` | `shipping` |
| `build_product_prompt` | `product` |
| `build_inventory_prompt` | `inventory` |
| `build_human_prompt` | `human` |
| `build_general_prompt` | `general` |

Each prompt includes:
1. **Persona**: "You are a friendly, empathetic customer support agent for EcoMarket"
2. **Grounding rule**: Explicit instruction not to invent facts
3. **Retrieved context** (RAG): Relevant chunks from the vectorstore
4. **Structured data** (when available): Order dict or product summary
5. **Few-shot examples**: 2 examples from `support_examples_enhanced.json`
6. **User question**: The raw user input

The grounding rule is the most important safety mechanism:

> "Answer ONLY based on the information provided below. Do NOT invent facts,
> policies, or product details. If the provided context does not contain
> enough information, say: 'I'm sorry, I don't have enough information...'"

---

### 2.8 `src/llm/llm_client.py` — LLM Generation

```python
def generate_llm_response(prompt: str, max_tokens: int = 350) -> str
```

Sends the completed prompt to Gemma 2B via the Ollama Python client.
- `temperature=0` for deterministic, factual responses
- `max_tokens=350` — increased from 220 to accommodate longer RAG-grounded answers
- Handles three error cases explicitly:
  - Model not found → instructs user to run `ollama pull`
  - Connection refused → instructs user to run `ollama serve`
  - Unexpected error → surfaces the raw error message

---

### 2.9 `src/core/utils.py` — Shared Utilities

```python
def extract_tracking_number(text: str) -> str | None  # regex: ECO + digits
def extract_product_id(text: str) -> str | None        # regex: P + 4 digits
def format_order_response(llm_answer, tracking, order) -> str  # Markdown card
```

Utility functions used by `app.py` to extract structured identifiers from
free text and format the order response with a rich Markdown card.

---

## 3. Streamlit App (`app.py`)

The app coordinates all modules:

1. **Initialization**: Loads the vectorstore with `@st.cache_resource` (once per session)
2. **Sidebar**: Shows detected intent, RAG status, and retrieved sources
3. **Chat history**: Persisted in `st.session_state.messages`
4. **Message handling**: Routes each message through the intent-specific pipeline
5. **Response display**: Renders Markdown responses with structured cards when available

### Session state variables

| Variable | Purpose |
|---|---|
| `messages` | Full chat history |
| `last_intent` | Detected intent for sidebar display |
| `last_sources` | Retrieved source metadata for sidebar |
| `rag_used` | Boolean flag for sidebar RAG status |

---

## 4. Limitations and Assumptions

### Limitations

1. **Keyword-based router**: The intent router uses simple keyword matching.
   Complex or ambiguous queries may be misclassified (e.g., "I want to return
   milk but my order hasn't arrived yet" could trigger `return_policy` instead
   of `order_status`).

2. **Gemma 2B capacity**: Gemma 2B is a small model (2 billion parameters).
   It may hallucinate if the retrieved context is insufficient, or produce
   vague answers for complex policy questions. The grounding rules mitigate
   this but cannot eliminate it entirely.

3. **No conversation memory**: Each query is handled independently. The LLM
   does not have access to previous messages in the conversation. Adding
   LangChain `ConversationBufferMemory` would be the next logical upgrade.

4. **Static inventory**: The inventory DataFrame is loaded and cached at startup.
   If the Excel file is updated while the app is running, the cache must be cleared.

5. **PDF text extraction quality**: `pypdf` may produce imperfect text from
   scanned PDFs or PDFs with complex layouts. If extraction quality is poor,
   upgrading to `pymupdf` (fitz) is recommended.

6. **FAISS does not support real-time updates**: Adding new documents requires
   rebuilding the entire index (`force_rebuild=True`).

### Assumptions

- All data files are stored in the `data/` directory.
- Ollama is running locally at `http://127.0.0.1:11434`.
- The `gemma2:2b` model has been pulled with `ollama pull gemma2:2b`.
- The first app run will take 1–3 minutes to build and save the vectorstore.
- Subsequent runs load the saved index in under 5 seconds.

---

## 5. Request Flow Example

**User query:** "Where is my order ECO20105?"

1. `detect_intent("where is my order eco20105")` → `"order_status"`
2. `extract_tracking_number(...)` → `"ECO20105"`
3. `get_order("ECO20105")` → order dict (status, items, shipping method, etc.)
4. `retrieve_context_text("where is my order ECO20105", vectorstore, k=3)` → shipping policy chunks
5. `build_order_prompt(order, user_input, rag_context)` → full prompt
6. `generate_llm_response(prompt)` → LLM natural-language answer
7. `format_order_response(llm_answer, tracking, order)` → answer + Markdown order card
8. Streamlit displays the response; sidebar shows intent and retrieved sources
