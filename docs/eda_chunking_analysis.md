# EDA: Chunking Strategy Analysis

## Purpose

This document records the chunking parameters used in the EcoMarket RAG pipeline
(`src/rag_pipeline.py`). All values were derived empirically from the actual knowledge-base
files using `notebooks/eda_chunking_analysis.ipynb`, which is the **source of truth** for
this analysis.

---

## 1. Dataset Overview (measured)

| Source | Type | Raw docs | Total chars | Avg chars/doc |
|---|---|---|---|---|
| `EcoMarket ReturnPolicy.pdf` | PDF | 2 pages | 3,327 | 1,664 |
| `EcoMarket ShippingPolicy.pdf` | PDF | 1 page | 1,627 | 1,627 |
| `inventory_200_products_named.xlsx` | Excel rows | 200 rows | ~50,500 | 253 |
| `product_catalog.xlsx` | Excel rows | 200 rows | ~53,520 | 268 |
| `orders_enhanced.json` | JSON records | 30 orders | ~8,418 | 281 |

**Total raw documents:** 433  
**Total characters:** ~117,392

---

## 2. Character Distribution by Source

### PDF policy documents

Both PDFs are dense: each page packs multiple numbered clauses into a single block of text.

**`EcoMarket ReturnPolicy.pdf` — 2 pages**

| Page | Chars | Words |
|---|---|---|
| 1 | 1,907 | 294 |
| 2 | 1,420 | 213 |

**`EcoMarket ShippingPolicy.pdf` — 1 page**

| Page | Chars | Words |
|---|---|---|
| 1 | 1,627 | 234 |

Both pages far exceed any reasonable `chunk_size` threshold — splitting is expected and
desirable for clause-level retrieval granularity.

### Excel rows (inventory / catalog)

Both sources are serialised as pipe-delimited key-value strings by the loader.

| Source | Min chars | Max chars | Mean chars | Std |
|---|---|---|---|---|
| `inventory_200_products_named.xlsx` | 238 | 274 | 253 | 7.4 |
| `product_catalog.xlsx` | 245 | 305 | 268 | 11.9 |

All rows are compact and low-variance. They are **never split** — each row is one
self-contained atomic chunk.

### JSON orders

| Metric | Value |
|---|---|
| Records | 30 |
| Min chars | 209 |
| Max chars | 341 |
| Mean chars | 281 |
| Std | 45.5 |

Orders are the **largest structured source** by maximum document length (341 chars).
This maximum becomes the hard floor for `chunk_size`: any value below 341 would split
an order record, separating its fields and degrading retrieval quality.

---

## 3. Word Distribution

| Source | Avg words/doc |
|---|---|
| Return policy pages | 254 |
| Shipping policy page | 234 |
| Inventory rows | ~39 |
| Product catalog rows | ~41 |
| Orders | ~44 |

---

## 4. Corpus Composition

```
EcoMarket ReturnPolicy.pdf  :   2 docs  (0.5% of raw docs,  2.8% of chars)
EcoMarket ShippingPolicy.pdf:   1 doc   (0.2%,              1.4%)
inventory                   : 200 docs (46.2%,             43.0%)
product_catalog             : 200 docs (46.2%,             45.6%)
orders                      :  30 docs  (6.9%,              7.2%)
```

The corpus is dominated in **document count** by structured rows (inventory + catalog),
which account for over 92% of raw documents. PDF pages are the minority by count but
are the only source that requires splitting.

---

## 5. Chunking Strategy Decision

### Key constraint: structured record integrity

The maximum structured document length is **341 characters** (orders). Any `chunk_size`
below this value would split an order record mid-content, destroying the structured
context needed for retrieval. This is the empirical floor.

### Candidate evaluation

Three candidates were tested, each with overlap set at 12% of `chunk_size`:

| `chunk_size` | `chunk_overlap` | Structured splits | PDF chunks | Total chunks |
|---|---|---|---|---|
| 341 | 40 | 0 | 18 | 448 |
| **391** | **45** | **0** | **15** | **445** |
| 441 | 55 | 0 | 14 | 444 |

`chunk_size=341` (the exact floor) leaves zero safety margin — a single new order
record above 341 chars would trigger a split. `chunk_size=441` produces nearly the
same total chunk count as 391 but merges more clauses per PDF chunk, coarsening
retrieval granularity. `chunk_size=391` balances intact structured records, fine-grained
PDF chunks, and a 50-char safety margin above the current floor.

### Selected parameters

```python
chunk_size    = 391   # characters
chunk_overlap = 45    # characters
```

### Rationale

**chunk_size = 391**

- Derived as `max_structured (341) + 50 safety margin`.
- All inventory rows (238–274 chars), catalog rows (245–305 chars), and orders
  (209–341 chars) are below 391 and are **never split**.
- PDF pages (1,420–1,907 chars) produce approximately **5 chunks each** at this size,
  keeping related clauses within the same chunk while separating unrelated ones —
  which is the desired retrieval granularity.
- 391 chars ≈ **98 tokens** in English — well within the 256-token limit of
  `sentence-transformers/all-MiniLM-L6-v2`.

**chunk_overlap = 45**

- Set at 12% of `chunk_size` (~11 words).
- Sufficient to carry the tail of one PDF clause into the next chunk, preventing
  an isolated chunk that references context from the preceding section.
- Structured sources are never split, so overlap has no effect on them.

### Splitter configuration

```python
RecursiveCharacterTextSplitter(
    chunk_size=391,
    chunk_overlap=45,
    separators=["\n\n", "\n", ". ", " ", ""],
)
```

The separator priority (`\n\n` → `\n` → sentence → word → character) means the
splitter breaks at paragraph boundaries first, then at numbered clause line breaks,
before falling back to mid-sentence splits. Both policy PDFs use numbered clauses
separated by newlines, so the majority of splits occur at clean clause boundaries.

---

## 6. Post-Split Chunk Count (validated)

| Source | Raw docs | Chunks | Split? |
|---|---|---|---|
| Return policy | 2 pages | 10 | Yes (~5 per page) |
| Shipping policy | 1 page | 5 | Yes |
| Inventory | 200 rows | 200 | No |
| Product catalog | 200 rows | 200 | No |
| Orders | 30 records | 30 | No |
| **Total** | **433** | **445** | |

---

## 7. Conclusion

The selected values `chunk_size=391` and `chunk_overlap=45` are derived from the
measured character distributions of the actual knowledge-base files:

- The hard floor is **341 chars** — the maximum order record length. `chunk_size=391`
  adds a 50-char safety margin above this floor.
- All structured records (inventory, catalog, orders) remain atomic — **0 splits**.
- PDF pages (1,420–1,907 chars) produce **5 chunks each** at clause-level granularity.
- 391 chars ≈ 98 tokens, safely within `all-MiniLM-L6-v2`'s 256-token limit.
- The corpus produces **445 chunks** after splitting (from 433 raw documents,
  an expansion ratio of 1.03×).
