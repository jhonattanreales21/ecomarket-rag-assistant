"""EcoMarket RAG-based Customer Support Assistant.

Streamlit app that combines intent routing, structured data lookup,
and RAG retrieval to generate grounded responses via Gemma 2B.
"""

import streamlit as st

from src.rag_pipeline import get_vectorstore
from src.ui_blocks.chat_handler import handle_message
from src.ui_blocks.sidebar import render_sidebar

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

render_sidebar(vectorstore)

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
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.spinner("Thinking…"):
        answer, sources, intent, rag_used = handle_message(user_input, vectorstore)

    st.session_state.last_intent = intent
    st.session_state.last_sources = sources
    st.session_state.rag_used = rag_used

    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)

    st.rerun()
