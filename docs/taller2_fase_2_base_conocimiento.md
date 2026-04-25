# Phase 2: Knowledge Base — Documents, Chunking, and Indexing

## Overview

This document describes the knowledge base used by the EcoMarket RAG system:
which documents were selected, why they matter for customer support, how they are
loaded and converted into LangChain Documents, the chunking strategy, and the
indexing process.

---

## 1. Selected Document Types

### 1.1 Returns Policy PDF (`returns_policy_extended.pdf`)

**Why it matters:**  
Return and refund questions are among the most common customer support interactions.
The extended policy contains detailed rules about eligibility windows, product
categories, hygiene product restrictions, damaged goods, and the step-by-step
return process.

**Without RAG:** The original system loaded the entire policy as a string and
injected it verbatim into the prompt. This wastes context window space and may
exceed the model's input limit for longer policies.

**With RAG:** Only the 3–4 most relevant policy sections are retrieved and included
in the prompt, keeping the context focused and reducing hallucination risk.

---

### 1.2 Shipping Policy PDF (`shipping_policy.pdf`)

**Why it matters:**  
Shipping questions (delivery times, international shipping, delay compensation,
free shipping thresholds, express vs. standard) are a second major category of
customer queries. The shipping policy is the authoritative source of truth for
these rules.

**Coverage:** Domestic and international shipping, estimated delivery times per
region, delay compensation rules, carrier information, and free shipping conditions.

---

### 1.3 Inventory Excel (`inventory_200_products_named.xlsx`)

**Why it matters:**  
Customers frequently ask about product availability, stock levels, perishability,
expiration dates, and shelf life — especially for food and personal care products.

**Structure:** 200 rows, one per product, with columns:
`product_id`, `product_name`, `category`, `batch`, `perishable`,
`manufacturing_date`, `expiration_date`, `shelf_life`, `stock`, `warehouse`.

**Approach:** Each row is converted to a pipe-delimited text document
(e.g., `Inventory record — product_id: P0001 | product_name: Organic Whole Milk | ...`).
Because rows are short (~150–180 chars), they remain as single chunks after splitting.

Additionally, `inventory_service.py` supports direct structured lookup by `product_id`
or partial name match — bypassing RAG for exact queries where precision matters more
than semantic similarity.

---

### 1.4 Product Catalog Excel (`product_catalog.xlsx`)

**Why it matters:**  
Product descriptions help customers understand what they are buying — ingredients,
materials, certifications, use cases, and sustainability claims. This content is
ideal for semantic retrieval because customers often phrase product questions
in varied ways.

**Approach:** Each row is converted to a text document preserving all catalog
fields. RAG retrieval enables fuzzy matching on product names and descriptions
even when the customer does not know the exact product ID.

---

### 1.5 Orders JSON (`orders_enhanced.json`)

**Why it matters:**  
Indexing orders as RAG documents serves two purposes:
1. Semantic search can surface order context when a tracking number is not provided
   (e.g., "my milk order is delayed").
2. It enables RAG to retrieve delay patterns and shipping method context alongside
   structured order lookups.

**Primary approach:** Structured lookup via `order_service.py` using the exact
tracking number. RAG is used as a secondary enrichment layer.

**Note:** Orders contain sensitive customer data (delivery addresses, payment info)
in a real system. In this prototype, orders contain only operational data and no
personal identifiers.

---

### 1.6 Support Examples JSON (`support_examples_enhanced.json`)

**Why it matters:**  
The enhanced support examples serve a dual purpose:
1. **Few-shot prompting:** 2–3 examples per intent are injected directly into
   prompts to guide the model's tone and format.
2. **RAG indexing:** Indexing all examples enables the system to retrieve
   similar past interactions, providing additional context for novel queries.

This is particularly useful for edge-case queries where no other document
type provides a direct match.

---

## 2. Document Loading Pipeline

All document loading is implemented in `src/rag/document_loader.py`.

### PDF loading

```python
from pypdf import PdfReader

reader = PdfReader(path)
for page in reader.pages:
    text = page.extract_text()
    Document(page_content=text, metadata={"doc_type": ..., "page": i+1})
```

Each page becomes one Document. `pypdf` handles text extraction from PDFs
without requiring any external system dependencies.

### Excel loading

```python
import pandas as pd

df = pd.read_excel(path, dtype=str)
for _, row in df.iterrows():
    text = "Record — " + " | ".join(f"{k}: {v}" for k, v in row.items())
    Document(page_content=text, metadata={...})
```

Converting all values to strings before joining prevents type errors
and preserves the full precision of date fields.

### JSON loading

```python
import json

with open(path) as f:
    records = json.load(f)

for record in records:
    text = build_text_from_record(record)
    Document(page_content=text, metadata={...})
```

Each JSON record (order, support example) is serialized into a readable
natural-language string before being indexed.

### Metadata preservation

Every Document carries metadata including:
- `source`: path to the original file
- `doc_type`: category label (enables filtered retrieval)
- Domain-specific fields: `product_id`, `tracking_number`, `intent`, `page`, etc.

---

## 3. Chunking Strategy

See `docs/eda_chunking_analysis.md` for the full EDA and justification.

**Summary:**

| Parameter | Value |
|---|---|
| Splitter | `RecursiveCharacterTextSplitter` |
| `chunk_size` | 700 characters |
| `chunk_overlap` | 100 characters |

The recursive splitter attempts to split on paragraph breaks (`\n\n`), then
line breaks (`\n`), then sentence boundaries (`. `), before falling back to
word and character splits. This preserves semantic coherence as much as possible.

Structured rows (inventory, catalog, orders, examples) are all shorter than
700 characters and are **never split** — they remain as single atomic chunks.

---

## 4. Indexing Process

The indexing process is managed by `src/rag/rag_pipeline.py`:

1. **Load documents** — `load_all_documents()` calls all six loaders.
2. **Chunk** — `RecursiveCharacterTextSplitter` splits long documents.
3. **Embed** — `HuggingFaceEmbeddings` with `all-MiniLM-L6-v2` converts each
   chunk into a 384-dimensional vector.
4. **Index** — `FAISS.from_documents()` builds the similarity index.
5. **Persist** — `vectorstore.save_local("vectorstore/faiss_index/")` saves
   the index to disk.
6. **Reload** — On subsequent app starts, `FAISS.load_local()` skips the
   build step entirely.

**Triggering a rebuild:** Pass `force_rebuild=True` to `get_vectorstore()` or
delete the `vectorstore/` directory.

---

## 5. Summary: Why These Documents?

| Document | Customer queries it answers |
|---|---|
| Returns policy | Can I return this? What is the deadline? Can I return opened products? |
| Shipping policy | How long does delivery take? Do you ship internationally? Is shipping free? |
| Inventory | Is this product in stock? Is it perishable? When does it expire? |
| Product catalog | What is this product made of? Is it organic? Is it eco-friendly? |
| Orders | Where is my order? Why is it delayed? What did I order? |
| Support examples | Tone guidance, few-shot grounding for the LLM |

Together, these six sources cover the vast majority of EcoMarket customer
support queries and provide the factual grounding necessary to prevent
the LLM from hallucinating business-critical information.
