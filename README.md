# EcoMarket RAG Assistant

![Status](https://img.shields.io/badge/status-proposal-yellow)
![Domain](https://img.shields.io/badge/domain-e--commerce-blue)
![Model](https://img.shields.io/badge/model-Gemma%202B-orange)
![Interface](https://img.shields.io/badge/interface-Streamlit-red)

**Authors**

| Name | Email |
|---|---|
| Andres Cano | andres.cano.consulting@gmail.com |
| Jhonattan Reales | jhonatanreales21@gmail.com |

---

## Overview

EcoMarket RAG Assistant is a hybrid intent-based customer support chatbot built for EcoMarket, a fictional sustainable products e-commerce company. The system automates responses to the most frequent support queries — order tracking, return policies, and general questions — while routing complaints and sensitive cases to a human agent.

The architecture deliberately separates **structured data retrieval** from **language generation** to prevent the LLM from hallucinating business-critical information such as order statuses or return rules.

---

## How It Works

```
User message (Streamlit)
  → Intent detection     — keyword-based router classifies the query
  → Data retrieval       — order DB or return policy loaded as needed
  → Prompt construction  — few-shot examples injected alongside the data
  → LLM generation       — Gemma 2B via Ollama (temperature = 0)
  → Response displayed   — structured card + natural language reply
```

**Four supported intents:**

| Intent | Trigger keywords | What the bot does |
|---|---|---|
| `order_status` | "order", "tracking", "pedido" | Looks up the order and reports its status |
| `return_policy` | "return", "refund", "devol" | Answers based on the return policy document |
| `human` | "complaint", "queja" | Acknowledges frustration and escalates to a human agent |
| `general` | anything else | Responds helpfully within the EcoMarket context |

---

## Tech Stack

| Component | Technology |
|---|---|
| UI | Streamlit |
| LLM | Gemma 2B (via Ollama) |
| Prompt strategy | Few-shot prompting |
| Data layer | JSON (orders) + Markdown (policy) |
| Package manager | uv |

---

## Project Structure

```
ecomarket-rag-assistant/
├── app.py                    # Streamlit entry point
├── src/
│   ├── router.py             # Intent detection
│   ├── order_service.py      # Order lookup logic
│   ├── returns_service.py    # Return policy loader
│   ├── prompts.py            # Prompt builders (one per intent)
│   ├── llm_client.py         # Ollama client wrapper
│   └── utils_format.py       # Response formatting helpers
├── data/
│   ├── orders.json           # 10 mock orders (ECO1001–ECO1010)
│   ├── returns_policy.md     # Return rules injected into prompts
│   └── support_examples.json # Few-shot examples for all intents
└── docs/                     # Academic documentation (in Spanish)
```

---

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) — fast Python package manager
- [Ollama](https://ollama.com) — local LLM runtime

---

## Setup & Run

> **Before you start:** Ollama must be installed on your machine. Download it from [ollama.com](https://ollama.com) and follow the instructions for your OS:
>
> | OS | Installation |
> |---|---|
> | **macOS** | Download the `.dmg` from ollama.com or run `brew install ollama` |
> | **Windows** | Download the `.exe` installer from ollama.com or run `winget install Ollama.Ollama` |
> | **Linux** | `curl -fsSL https://ollama.com/install.sh \| sh` |
>
> Verify the installation with `ollama --version` before proceeding.

### 1. Clone the repository

```bash
git clone <repository-url>
cd ecomarket-rag-assistant
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Download the model

```bash
ollama pull gemma2:2b
```

### 4. Start the Ollama server

Open a terminal and keep it running in the background:

```bash
ollama serve
```

> If you see `address already in use`, the server is already running — you can skip this step.

### 5. Launch the app

Open a second terminal and run:

```bash
uv run streamlit run app.py
```

The chat interface will be available at **http://localhost:8501**

---

## Interacting with the Bot

Once the app is running, type your message in the chat input at the bottom. Some examples to try:

| Example message | Intent triggered |
|---|---|
| `"Where is my order ECO1005?"` | `order_status` |
| `"I want to return a product I bought last week"` | `return_policy` |
| `"I want to return an opened hygiene product"` | `return_policy` |
| `"I am very frustrated, nobody has helped me"` | `human` (escalation) |
| `"What kind of products does EcoMarket sell?"` | `general` |

The sidebar shows which intent was detected for each message, which is useful for understanding how the routing logic works.

---

## Documentation

Design decisions, risk analysis, ethical considerations, and prompt engineering results are documented in the [`docs/`](docs/) folder.

> **Note:** All documents are written in Spanish as part of an academic deliverable.

| File | Content |
|---|---|
| [`taller_1_fase_1_modelo_y_arquitectura.md`](docs/taller_1_fase_1_modelo_y_arquitectura.md) | Model selection rationale and system architecture |
| [`taller_1_fase_2_riesgos_y_etica.md`](docs/taller_1_fase_2_riesgos_y_etica.md) | Risks, ethics, and limitations |
| [`taller_1_fase_3_Ingenieria_de_prompts_&_evaluacion.md`](docs/taller_1_fase_3_Ingenieria_de_prompts_&_evaluacion.md) | Prompt engineering approach and evaluation results |

---

## Acknowledgments

This project was developed as part of the Master's program in Applied Artificial Intelligence at ICESI University. Special thanks to our tutors and peers for their guidance and feedback.
