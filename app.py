"""EcoMarket RAG-based Customer Support Assistant.

Streamlit app that combines intent routing, structured data lookup,
and RAG retrieval to generate grounded responses via Gemma 2B.
"""

import streamlit as st

# Internal modules
from src.router import detect_intent
from src.order_service import get_order
from src.inventory_service import (
    get_product_by_id,
    get_products_by_name,
    format_product_summary,
)
from src.rag_pipeline import get_vectorstore
from src.retriever import retrieve_context_text
from src.prompts import (
    build_order_prompt,
    build_return_prompt,
    build_shipping_prompt,
    build_product_prompt,
    build_inventory_prompt,
    build_human_prompt,
    build_general_prompt,
)
from src.llm_client import generate_llm_response
from src.utils import extract_tracking_number, extract_product_id, format_order_response

# ── page configuration ────────────────────────────────────────────────────────

st.set_page_config(
    page_title="EcoMarket Support Assistant",
    page_icon="🌿",
    layout="wide",
)

# ── vectorstore initialisation (cached for the session) ───────────────────────


@st.cache_resource(show_spinner="Loading knowledge base…")
def load_vectorstore():
    """Load or build the FAISS vectorstore once per session."""
    try:
        return get_vectorstore()
    except Exception as e:
        st.error(
            f"Could not load the knowledge base: {e}\n\n"
            "Make sure the data files are present in the `data/` folder."
        )
        return None


vectorstore = load_vectorstore()

# ── session state initialisation ─────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_intent" not in st.session_state:
    st.session_state.last_intent = "None"

if "last_sources" not in st.session_state:
    st.session_state.last_sources = []

if "rag_used" not in st.session_state:
    st.session_state.rag_used = False

# ── sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🌿 EcoMarket")
    st.subheader("System Info")
    st.markdown(f"**Detected intent:** `{st.session_state.last_intent}`")
    st.markdown(f"**RAG context used:** {'Yes' if st.session_state.rag_used else 'No'}")

    if vectorstore is not None:
        st.success("Knowledge base loaded", icon="✅")
    else:
        st.error("Knowledge base not available", icon="❌")

    st.divider()
    st.caption("Powered by Gemma 2B · FAISS · LangChain")

    if st.session_state.last_sources:
        with st.expander("Retrieved sources"):
            for src in st.session_state.last_sources:
                st.markdown(
                    f"- **{src.get('doc_type', '?')}** "
                    f"(score: {src.get('score', '?')}) — "
                    f"`{src.get('source', '?').split('/')[-1]}`"
                )

# ── page header ───────────────────────────────────────────────────────────────

st.title("EcoMarket Support Assistant")
st.caption("Ask me about your orders, returns, shipping, products, or inventory.")

# ── render previous messages ──────────────────────────────────────────────────

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── chat input ────────────────────────────────────────────────────────────────

user_input = st.chat_input("How can I help you today?")

if user_input:
    # Display user message immediately
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Intent detection and routing
    intent = detect_intent(user_input)
    st.session_state.last_intent = intent
    st.session_state.rag_used = False
    st.session_state.last_sources = []

    with st.spinner("Thinking…"):
        answer = ""
        sources: list[dict] = []

        # ── order status ──────────────────────────────────────────────────────
        if intent == "order_status":
            tracking = extract_tracking_number(user_input)

            if tracking:
                order = get_order(tracking)
                if order:
                    # Enrich with shipping/returns context from RAG
                    rag_context = ""
                    if vectorstore is not None:
                        rag_context, sources = retrieve_context_text(
                            user_input, vectorstore, k=3
                        )
                        st.session_state.rag_used = bool(rag_context)

                    prompt = build_order_prompt(order, user_input, rag_context)
                    llm_answer = generate_llm_response(prompt)
                    answer = format_order_response(llm_answer, tracking, order)
                else:
                    answer = (
                        f"I could not find order **{tracking}** in our system. "
                        "Please double-check the tracking number and try again."
                    )
            else:
                answer = (
                    "Please provide your order tracking number (e.g. **ECO20105**) "
                    "so I can look it up for you."
                )

        # ── return policy ─────────────────────────────────────────────────────
        elif intent == "return_policy":
            if vectorstore is not None:
                rag_context, sources = retrieve_context_text(
                    user_input, vectorstore, k=4, filter_doc_type="returns_policy"
                )
                # Fallback: broaden search if no policy chunks found
                if not rag_context:
                    rag_context, sources = retrieve_context_text(
                        user_input, vectorstore, k=4
                    )
                st.session_state.rag_used = bool(rag_context)
            else:
                rag_context = "Return policy context is currently unavailable."

            prompt = build_return_prompt(user_input, rag_context)
            answer = generate_llm_response(prompt)

        # ── shipping ──────────────────────────────────────────────────────────
        elif intent == "shipping":
            if vectorstore is not None:
                rag_context, sources = retrieve_context_text(
                    user_input, vectorstore, k=4, filter_doc_type="shipping_policy"
                )
                if not rag_context:
                    rag_context, sources = retrieve_context_text(
                        user_input, vectorstore, k=4
                    )
                st.session_state.rag_used = bool(rag_context)
            else:
                rag_context = "Shipping policy context is currently unavailable."

            prompt = build_shipping_prompt(user_input, rag_context)
            answer = generate_llm_response(prompt)

        # ── inventory ─────────────────────────────────────────────────────────
        elif intent == "inventory":
            product_summary = ""

            # Try structured lookup first
            pid = extract_product_id(user_input)
            if pid:
                product = get_product_by_id(pid)
                if product:
                    product_summary = format_product_summary(product)

            # Name-based search: try multi-word phrases (longest first) to avoid
            # short-word substring false positives (e.g. "is" matching "d[is]h")
            if not product_summary:
                _STOPWORDS = {
                    "what",
                    "is",
                    "the",
                    "of",
                    "a",
                    "an",
                    "how",
                    "does",
                    "do",
                    "tell",
                    "me",
                    "about",
                    "for",
                    "in",
                    "on",
                    "at",
                    "its",
                    "are",
                    "was",
                    "were",
                    "will",
                    "would",
                    "could",
                    "should",
                    "which",
                    "have",
                    "has",
                    "can",
                    "any",
                    "some",
                    "this",
                    "that",
                    "your",
                }
                content_words = [
                    w.strip("?.,!")
                    for w in user_input.split()
                    if w.strip("?.,!").lower() not in _STOPWORDS
                    and len(w.strip("?.,!")) > 2
                ]
                for length in range(len(content_words), 0, -1):
                    for start in range(len(content_words) - length + 1):
                        phrase = " ".join(content_words[start : start + length])
                        candidates = get_products_by_name(phrase)
                        if candidates:
                            product_summary = format_product_summary(candidates[0])
                            break
                    if product_summary:
                        break

            # RAG enrichment
            if vectorstore is not None:
                rag_context, sources = retrieve_context_text(
                    user_input, vectorstore, k=4
                )
                st.session_state.rag_used = bool(rag_context)
            else:
                rag_context = ""

            if not product_summary and not rag_context:
                answer = (
                    "I couldn't find that product in our inventory. "
                    "Please provide the product ID (e.g. **P0001**) or a product name."
                )
            else:
                prompt = build_inventory_prompt(
                    user_input, rag_context, product_summary
                )
                answer = generate_llm_response(prompt)

                # Append structured card if we have it
                if product_summary:
                    answer += f"\n\n---\n\n**Product record:**\n{product_summary}"

        # ── product information ───────────────────────────────────────────────
        elif intent == "product":
            if vectorstore is not None:
                rag_context, sources = retrieve_context_text(
                    user_input, vectorstore, k=4, filter_doc_type="product_catalog"
                )
                if not rag_context:
                    rag_context, sources = retrieve_context_text(
                        user_input, vectorstore, k=4
                    )
                st.session_state.rag_used = bool(rag_context)
            else:
                rag_context = ""

            prompt = build_product_prompt(user_input, rag_context)
            answer = generate_llm_response(prompt)

        # ── human escalation ──────────────────────────────────────────────────
        elif intent == "human":
            prompt = build_human_prompt(user_input)
            answer = generate_llm_response(prompt)

        # ── general / catch-all ───────────────────────────────────────────────
        else:
            if vectorstore is not None:
                rag_context, sources = retrieve_context_text(
                    user_input, vectorstore, k=4
                )
                st.session_state.rag_used = bool(rag_context)
            else:
                rag_context = ""

            prompt = build_general_prompt(user_input, rag_context)
            answer = generate_llm_response(prompt)

        # Store retrieved sources for sidebar display
        st.session_state.last_sources = sources

    # Display assistant response
    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)

    # Force sidebar to refresh by rerunning
    st.rerun()

    with st.chat_message("assistant"):
        st.markdown(answer)
