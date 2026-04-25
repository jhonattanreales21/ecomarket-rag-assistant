# EcoMarket RAG Assistant

![Status](https://img.shields.io/badge/status-wip-yellow)
![Domain](https://img.shields.io/badge/domain-e--commerce-blue)
![Model](https://img.shields.io/badge/model-Gemma%202B-orange)
![Interface](https://img.shields.io/badge/interface-Streamlit-red)
![RAG](https://img.shields.io/badge/RAG-FAISS%20%2B%20LangChain-purple)

**Authors**

| Name | Email |
|---|---|
| Andres Cano | andres.cano.consulting@gmail.com |
| Jhonattan Reales | jhonatanreales21@gmail.com |

---

## Overview

EcoMarket RAG Assistant is a hybrid customer support chatbot for EcoMarket, a sustainable
products e-commerce company. The system combines **intent-based routing**, **structured data
lookup**, and a **full RAG pipeline** to generate factually grounded responses via Gemma 2B.

The architecture deliberately separates **structured data retrieval** (orders, inventory)
from **language generation** to prevent the LLM from hallucinating business-critical
information such as order statuses, return rules, or product expiration dates.

---

## How It Works

```
User message (Streamlit)
  → Intent detection     — keyword-based router (7 intents)
  → Structured lookup    — orders (JSON) or inventory (Excel) when applicable
  → RAG retrieval        — top-4 relevant chunks from FAISS knowledge base
  → Prompt construction  — retrieved context + structured data + few-shot examples
  → LLM generation       — Gemma 2B via Ollama (temperature = 0)
  → Response displayed   — natural language answer + structured data card
```

**Seven supported intents:**

| Intent | Trigger keywords | What the bot does |
|---|---|---|
| `order_status` | "order", "tracking", "ECO…" | Structured order lookup + shipping context |
| `return_policy` | "return", "refund", "exchange" | RAG over returns policy PDF |
| `shipping` | "shipping", "delivery", "international" | RAG over shipping policy PDF |
| `inventory` | "stock", "available", "perishable", "expire", "P00…" | Structured inventory lookup + RAG |
| `product` | "product", "organic", "bamboo", "catalog" | RAG over product catalog |
| `human` | "complaint", "upset", "angry", "escalate" | Escalation — no data lookup |
| `general` | anything else | RAG over full knowledge base |

---

## Tech Stack

| Component | Technology |
|---|---|
| UI | Streamlit |
| LLM | Gemma 2B (via Ollama) |
| RAG orchestration | LangChain |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` |
| Vector store | FAISS (local, persistent) |
| Chunking | `RecursiveCharacterTextSplitter` (391 chars / 45 overlap) |
| Structured data | pandas + openpyxl (inventory), JSON (orders) |
| PDF loading | pypdf |
| Package manager | uv |

---

## Project Structure

```
ecomarket-rag-assistant/
├── app.py                              # Streamlit entry point
├── pyproject.toml                      # uv dependencies
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── router.py                   # Intent detection (7 intents)
│   │   └── utils.py                    # Tracking extraction, formatters
│   ├── llm/
│   │   ├── llm_client.py               # Ollama client wrapper
│   │   └── prompts.py                  # Prompt builders (one per intent)
│   ├── rag/
│   │   ├── document_loader.py          # PDF, Excel, JSON → LangChain Documents
│   │   ├── rag_pipeline.py             # Build / load FAISS vectorstore
│   │   └── retriever.py                # Similarity search wrapper
│   ├── services/
│   │   ├── inventory_service.py        # Structured inventory lookup
│   │   └── order_service.py            # Structured order lookup
│   └── ui_blocks/
│       ├── chat_handler.py             # Intent router + response orchestrator
│       └── sidebar.py                  # Streamlit sidebar rendering
├── data/
│   ├── EcoMarket ReturnPolicy.pdf
│   ├── EcoMarket ShippingPolicy.pdf
│   ├── inventory_200_products_named.xlsx
│   ├── product_catalog.xlsx
│   ├── orders_enhanced.json            # 30 realistic orders
│   └── support_examples_enhanced.json  # Few-shot examples
├── vectorstore/
│   └── faiss_index/                    # Auto-generated on first run
└── docs/

```

---

## Prerequisites

- Python 3.10 or 3.11
- [uv](https://github.com/astral-sh/uv) — fast Python package manager
- [Ollama](https://ollama.com) — local LLM runtime

---

## Setup & Run

### 1. Install uv (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or on macOS with Homebrew:

```bash
brew install uv
```

### 2. Install Ollama

Download from [ollama.com](https://ollama.com) or:

| OS | Command |
|---|---|
| macOS | `brew install ollama` |
| Linux | `curl -fsSL https://ollama.com/install.sh \| sh` |
| Windows | Download the `.exe` from ollama.com |

Verify: `ollama --version`

### 3. Clone the repository

```bash
git clone <repository-url>
cd ecomarket-rag-assistant
```

### 4. Install dependencies

```bash
uv sync
```

This installs all packages including LangChain, FAISS, sentence-transformers,
pandas, pypdf, and Streamlit.

> **Note:** The first `uv sync` will download PyTorch and sentence-transformers
> (~1.5 GB). This only happens once.

### 5. Add data files

Place the following files in the `data/` directory:

```
data/
├── EcoMarket ReturnPolicy.pdf
├── EcoMarket ShippingPolicy.pdf
├── inventory_200_products_named.xlsx   
├── product_catalog.xlsx                
├── orders_enhanced.json                
└── support_examples_enhanced.json      
```

### 6. Pull the Gemma 2B model

```bash
ollama pull gemma2:2b
```

### 7. Start the Ollama server

Open a terminal and keep it running:

```bash
ollama serve
```

> If you see `address already in use`, Ollama is already running — skip this step.

### 8. Launch the app

In a second terminal:

```bash
uv run streamlit run app.py
```

Open **http://localhost:8501** in your browser.

> **First run:** The app will build the FAISS vectorstore (embedding ~600 chunks).
> This takes 1–3 minutes and only happens once. Subsequent starts load from disk in < 5 seconds.

---

## Example Questions

| Question | Intent triggered |
|---|---|
| `Where is my order ECO20105?` | `order_status` |
| `Why is my order ECO20111 delayed?` | `order_status` |
| `Does my order ECO20120 contain perishable products?` | `order_status` |
| `Can I return an opened hygiene product?` | `return_policy` |
| `What is the return window for electronics?` | `return_policy` |
| `What is the shipping policy for delayed orders?` | `shipping` |
| `Do you ship internationally?` | `shipping` |
| `How long does standard shipping take?` | `shipping` |
| `Is product P0001 available in stock?` | `inventory` |
| `Is Organic Whole Milk perishable?` | `inventory` |
| `What is the expiration date of product P0003?` | `inventory` |
| `Tell me about the Natural Bamboo Toothbrush` | `product` |
| `What sustainable cleaning products do you have?` | `product` |
| `What should I do if my product arrived damaged?` | `return_policy` |
| `I am very upset and want to complain` | `human` (escalation) |

---

## Rebuilding the Vectorstore

If you update any data files, rebuild the FAISS index:

```python
# In a Python shell or script
from src.rag_pipeline import get_vectorstore
get_vectorstore(force_rebuild=True)
```

Or simply delete the `vectorstore/` directory and restart the app.

---

## Documentation

### Taller 1 — Baseline Chatbot (`docs/taller1/`)

| File | Content |
|---|---|
| [docs/taller1/taller_1_fase_1_modelo_y_arquitectura.md](docs/taller1/taller_1_fase_1_modelo_y_arquitectura.md) | Model selection, MVP vs. target architecture |
| [docs/taller1/taller_1_fase_2_riesgos_y_etica.md](docs/taller1/taller_1_fase_2_riesgos_y_etica.md) | Risks, ethics, and limitations of the baseline system |
| [docs/taller1/taller_1_fase_3_Ingenieria_de_prompts_&_evaluacion.md](docs/taller1/taller_1_fase_3_Ingenieria_de_prompts_&_evaluacion.md) | Prompt engineering design and evaluation |

### Taller 2 — RAG Extension (`docs/`)

| File | Content |
|---|---|
| [docs/taller2_fase_1_rag_componentes.md](docs/taller2_fase_1_rag_componentes.md) | Embedding model and vector store selection rationale |
| [docs/taller2_fase_2_base_conocimiento.md](docs/taller2_fase_2_base_conocimiento.md) | Knowledge base, chunking strategy, indexing process |
| [docs/taller2_fase_3_integracion_codigo.md](docs/taller2_fase_3_integracion_codigo.md) | End-to-end code walkthrough, limitations, example flow |
| [docs/eda_chunking_analysis.md](docs/eda_chunking_analysis.md) | EDA-based chunking justification (chunk_size=391, overlap=45) |

---

## Acknowledgments

This project was developed as part of the Master's program in Applied Artificial
Intelligence at ICESI University. Special thanks to our tutors and peers for
their guidance and feedback.

