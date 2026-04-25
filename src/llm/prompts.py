"""Prompt builders for the EcoMarket RAG assistant.

Each builder constructs a self-contained prompt for Gemma 2B that includes:
- A role / persona description
- Strict grounding rules (no hallucination)
- Retrieved RAG context (when available)
- Structured data (orders, inventory) when directly relevant
- Few-shot examples from support_examples_enhanced.json
- The user's current question
"""

import json
from pathlib import Path

EXAMPLES_PATH = Path("data/support_examples_enhanced.json")

# ── few-shot helpers ──────────────────────────────────────────────────────────


def _load_examples() -> list[dict]:
    """Load all few-shot examples from the enhanced JSON file."""
    if not EXAMPLES_PATH.exists():
        return []
    with open(EXAMPLES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _format_examples(intent: str, max_examples: int = 2) -> str:
    """Return formatted few-shot blocks for the given intent."""
    examples = _load_examples()
    selected = [e for e in examples if e.get("intent") == intent][:max_examples]
    if not selected:
        return ""

    header = "--- Few-shot examples ---"
    blocks = [header]
    for ex in selected:
        blocks.append(
            f"Customer: {ex['customer_query']}\n"
            f"Assistant: {ex['assistant_response']}"
        )
    blocks.append("--- End of examples ---")
    return "\n\n".join(blocks)


# ── shared persona / rules ────────────────────────────────────────────────────

_PERSONA = (
    "You are a friendly, empathetic, and professional customer support agent for EcoMarket, "
    "a sustainable products e-commerce company."
)

_GROUNDING_RULE = (
    "IMPORTANT: Answer ONLY based on the information provided below. "
    "Do NOT invent facts, policies, or product details. "
    "If the provided context does not contain enough information to answer the question, "
    "say: \"I'm sorry, I don't have enough information to answer that question. "
    'Please contact our support team for assistance."'
)


# ── intent-specific prompt builders ──────────────────────────────────────────


def build_order_prompt(order: dict, user_query: str, rag_context: str = "") -> str:
    """Build a prompt for order status queries.

    Args:
        order: Structured order dict from orders_enhanced.json.
        user_query: The user's raw question.
        rag_context: Retrieved chunks from the vectorstore (optional).

    Returns:
        Formatted prompt string.
    """
    examples = _format_examples("order_status", max_examples=3)

    items = order.get("items", [])
    items_text = "\n".join(
        f"  - {it.get('product_name', '?')} x{it.get('quantity', '?')} "
        f"(perishable: {it.get('perishable', '?')})"
        for it in items
    )
    delay_reason = order.get("delay_reason", "No delay recorded.")

    rag_section = (
        f"\nRelevant policy / shipping context:\n{rag_context}\n" if rag_context else ""
    )

    return f"""{_PERSONA}

{_GROUNDING_RULE}

{examples}

Order data (authoritative — do not contradict this):
- Tracking number: {order['tracking_number']}
- Status: {order['status']}
- Order date: {order.get('order_date', 'N/A')}
- Estimated delivery: {order['estimated_delivery']}
- Shipping method: {order.get('shipping_method', 'N/A')}
- Region: {order.get('shipping_region', 'N/A')}
- Delay reason: {delay_reason}
- Items:
{items_text}
- Tracking link: {order.get('tracking_url', 'N/A')}
{rag_section}
Customer question: {user_query}

Write a concise, warm, and accurate response using only the data above.""".strip()


def build_return_prompt(user_query: str, rag_context: str) -> str:
    """Build a prompt for return policy queries, grounded in RAG context.

    Args:
        user_query: The user's raw question.
        rag_context: Retrieved chunks from the returns policy vectorstore.

    Returns:
        Formatted prompt string.
    """
    examples = _format_examples("return_policy", max_examples=3)

    return f"""{_PERSONA}

{_GROUNDING_RULE}

{examples}

Return policy context (retrieved from official documents):
{rag_context}

Customer question: {user_query}

Based strictly on the policy context above, provide a clear, empathetic answer.
If the return is eligible, explain the steps. If not, explain why respectfully.""".strip()


def build_shipping_prompt(user_query: str, rag_context: str) -> str:
    """Build a prompt for shipping policy queries.

    Args:
        user_query: The user's raw question.
        rag_context: Retrieved chunks from the shipping policy vectorstore.

    Returns:
        Formatted prompt string.
    """
    examples = _format_examples("shipping", max_examples=3)

    return f"""{_PERSONA}

{_GROUNDING_RULE}

{examples}

Shipping policy context (retrieved from official documents):
{rag_context}

Customer question: {user_query}

Based strictly on the shipping policy above, give a direct, helpful, and polite answer.""".strip()


def build_product_prompt(user_query: str, rag_context: str) -> str:
    """Build a prompt for product information queries.

    Args:
        user_query: The user's raw question.
        rag_context: Retrieved chunks from the product catalog vectorstore.

    Returns:
        Formatted prompt string.
    """
    examples = _format_examples("product", max_examples=3)

    return f"""{_PERSONA}

{_GROUNDING_RULE}

{examples}

Product catalog context (retrieved from official documents):
{rag_context}

Customer question: {user_query}

Describe the product clearly and concisely based only on the context above.""".strip()


def build_inventory_prompt(
    user_query: str,
    rag_context: str,
    product_summary: str = "",
) -> str:
    """Build a prompt for inventory / availability queries.

    Args:
        user_query: The user's raw question.
        rag_context: Retrieved chunks from the inventory vectorstore.
        product_summary: Structured product facts from inventory_service (optional).

    Returns:
        Formatted prompt string.
    """
    examples = _format_examples("inventory", max_examples=3)

    structured_section = (
        f"\nStructured inventory record (authoritative):\n{product_summary}\n"
        if product_summary
        else ""
    )

    return f"""{_PERSONA}

{_GROUNDING_RULE}

{examples}

Inventory context (retrieved):
{rag_context}
{structured_section}
Customer question: {user_query}

Answer with specific stock and product details based only on the data above.""".strip()


def build_human_prompt(user_query: str, rag_context: str = "") -> str:
    """Build an escalation prompt for upset or frustrated customers.

    Args:
        user_query: The user's raw question.
        rag_context: Optional retrieved support examples.

    Returns:
        Formatted prompt string.
    """
    examples = _format_examples("human", max_examples=3)

    return f"""{_PERSONA}

Your role right now is to acknowledge a frustrated customer and escalate to a human specialist.

Rules:
- Acknowledge the customer's feelings before anything else.
- Do NOT attempt to resolve the issue yourself.
- Reassure the customer that a human specialist will contact them.
- Do NOT make promises about timelines or outcomes.
- Keep the message brief, warm, and reassuring.

{examples}

Customer message: {user_query}

Write a short, empathetic escalation message.""".strip()


def build_general_prompt(user_query: str, rag_context: str = "") -> str:
    """Build a catch-all prompt for general customer questions.

    Args:
        user_query: The user's raw question.
        rag_context: Retrieved chunks from the vectorstore (optional).

    Returns:
        Formatted prompt string.
    """
    examples = _format_examples("general", max_examples=3)

    rag_section = (
        f"\nContext retrieved from knowledge base:\n{rag_context}\n"
        if rag_context
        else ""
    )

    return f"""{_PERSONA}

{_GROUNDING_RULE}

{examples}
{rag_section}
Customer question: {user_query}

Provide a helpful, concise, and accurate answer.
If the question is outside your scope, explain what you can help with.""".strip()
