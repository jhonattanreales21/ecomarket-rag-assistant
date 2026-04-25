"""Sidebar UI block for the EcoMarket Support Assistant."""

import streamlit as st


def render_sidebar(vectorstore) -> None:
    """Render the EcoMarket sidebar with system info and retrieved sources.

    Args:
        vectorstore: The loaded FAISS vectorstore, or None if unavailable.
    """
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
