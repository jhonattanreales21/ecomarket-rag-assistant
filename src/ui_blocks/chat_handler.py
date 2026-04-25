"""Intent routing and response generation for the EcoMarket Support Assistant."""

from src.core.router import detect_intent
from src.services.order_service import get_order
from src.services.inventory_service import get_product_by_id, get_products_by_name, format_product_summary
from src.rag.retriever import retrieve_context_text
from src.llm.prompts import (
    build_order_prompt,
    build_return_prompt,
    build_shipping_prompt,
    build_product_prompt,
    build_inventory_prompt,
    build_human_prompt,
    build_general_prompt,
)
from src.llm.llm_client import generate_llm_response
from src.core.utils import extract_tracking_number, extract_product_id, format_order_response

_STOPWORDS = {
    "what", "is", "the", "of", "a", "an", "how", "does", "do", "tell", "me",
    "about", "for", "in", "on", "at", "its", "are", "was", "were", "will",
    "would", "could", "should", "which", "have", "has", "can", "any", "some",
    "this", "that", "your",
}


def handle_message(
    user_input: str,
    vectorstore,
) -> tuple[str, list[dict], str, bool]:
    """Route a user message to the correct intent handler and return a grounded response.

    Detects the intent (order_status, return_policy, shipping, inventory, product,
    human, or general), runs the appropriate structured lookup and/or RAG retrieval,
    builds the prompt, and calls the LLM. When no vectorstore is available, handlers
    fall back to prompt-only generation or a static fallback message.

    Args:
        user_input: Raw message text from the user.
        vectorstore: Loaded FAISS vectorstore used for RAG retrieval, or None if
            the knowledge base failed to load (graceful degradation is applied).

    Returns:
        answer: Final response string to display to the user. May include a
            structured data card appended after the LLM answer (e.g. order or
            product details).
        sources: List of metadata dicts for each retrieved document chunk, each
            containing keys ``doc_type``, ``source``, and ``score``. Empty list
            when RAG was not used.
        intent: Detected intent string (e.g. ``"order_status"``).
        rag_used: True if at least one RAG chunk was retrieved and injected into
            the prompt.
    """
    intent = detect_intent(user_input)
    answer = ""
    sources: list[dict] = []
    rag_used = False

    # ── order status ──────────────────────────────────────────────────────────
    if intent == "order_status":
        tracking = extract_tracking_number(user_input)

        if tracking:
            order = get_order(tracking)
            if order:
                rag_context = ""
                if vectorstore is not None:
                    rag_context, sources = retrieve_context_text(user_input, vectorstore, k=3)
                    rag_used = bool(rag_context)
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

    # ── return policy ─────────────────────────────────────────────────────────
    elif intent == "return_policy":
        if vectorstore is not None:
            rag_context, sources = retrieve_context_text(
                user_input, vectorstore, k=4, filter_doc_type="returns_policy"
            )
            # Fallback: broaden search if no policy chunks found
            if not rag_context:
                rag_context, sources = retrieve_context_text(user_input, vectorstore, k=4)
            rag_used = bool(rag_context)
        else:
            rag_context = "Return policy context is currently unavailable."

        prompt = build_return_prompt(user_input, rag_context)
        answer = generate_llm_response(prompt)

    # ── shipping ──────────────────────────────────────────────────────────────
    elif intent == "shipping":
        if vectorstore is not None:
            rag_context, sources = retrieve_context_text(
                user_input, vectorstore, k=4, filter_doc_type="shipping_policy"
            )
            if not rag_context:
                rag_context, sources = retrieve_context_text(user_input, vectorstore, k=4)
            rag_used = bool(rag_context)
        else:
            rag_context = "Shipping policy context is currently unavailable."

        prompt = build_shipping_prompt(user_input, rag_context)
        answer = generate_llm_response(prompt)

    # ── inventory ─────────────────────────────────────────────────────────────
    elif intent == "inventory":
        product_summary = ""

        pid = extract_product_id(user_input)
        if pid:
            product = get_product_by_id(pid)
            if product:
                product_summary = format_product_summary(product)

        # Name-based search: try multi-word phrases (longest first) to avoid
        # short-word substring false positives (e.g. "is" matching "d[is]h")
        if not product_summary:
            content_words = [
                w.strip("?.,!")
                for w in user_input.split()
                if w.strip("?.,!").lower() not in _STOPWORDS and len(w.strip("?.,!")) > 2
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

        if vectorstore is not None:
            rag_context, sources = retrieve_context_text(user_input, vectorstore, k=4)
            rag_used = bool(rag_context)
        else:
            rag_context = ""

        if not product_summary and not rag_context:
            answer = (
                "I couldn't find that product in our inventory. "
                "Please provide the product ID (e.g. **P0001**) or a product name."
            )
        else:
            prompt = build_inventory_prompt(user_input, rag_context, product_summary)
            answer = generate_llm_response(prompt)

            if product_summary:
                answer += f"\n\n---\n\n**Product record:**\n{product_summary}"

    # ── product information ───────────────────────────────────────────────────
    elif intent == "product":
        if vectorstore is not None:
            rag_context, sources = retrieve_context_text(
                user_input, vectorstore, k=4, filter_doc_type="product_catalog"
            )
            if not rag_context:
                rag_context, sources = retrieve_context_text(user_input, vectorstore, k=4)
            rag_used = bool(rag_context)
        else:
            rag_context = ""

        prompt = build_product_prompt(user_input, rag_context)
        answer = generate_llm_response(prompt)

    # ── human escalation ──────────────────────────────────────────────────────
    elif intent == "human":
        prompt = build_human_prompt(user_input)
        answer = generate_llm_response(prompt)

    # ── general / catch-all ───────────────────────────────────────────────────
    else:
        if vectorstore is not None:
            rag_context, sources = retrieve_context_text(user_input, vectorstore, k=4)
            rag_used = bool(rag_context)
        else:
            rag_context = ""

        prompt = build_general_prompt(user_input, rag_context)
        answer = generate_llm_response(prompt)

    return answer, sources, intent, rag_used
