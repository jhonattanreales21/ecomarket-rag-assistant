"""Shared utilities for the EcoMarket RAG assistant.

Includes output formatters and tracking-number extraction helpers.
"""

import re


# ── order utilities ───────────────────────────────────────────────────────────


def extract_tracking_number(text: str) -> str | None:
    """Extract an EcoMarket tracking number from free text.

    Looks for the pattern ECO followed by digits (e.g. ECO20105).

    Args:
        text: Raw user input.

    Returns:
        Uppercase tracking number string, or None if not found.
    """
    match = re.search(r"\bECO\d+\b", text, re.IGNORECASE)
    if match:
        return match.group(0).upper()
    return None


def format_order_response(llm_answer: str, tracking: str, order: dict) -> str:
    """Combine the LLM's reply with a structured order details card.

    Args:
        llm_answer: Natural language response from the LLM.
        tracking: Tracking number string.
        order: Order dict from orders_enhanced.json.

    Returns:
        Markdown-formatted string with the LLM answer and order card.
    """
    items = order.get("items", [])
    items_lines = "\n".join(
        f"  - {it.get('product_name', '?')} x{it.get('quantity', '?')} "
        f"({'perishable' if it.get('perishable') else 'non-perishable'})"
        for it in items
    )
    delay_line = (
        f"\n- **Delay reason:** {order['delay_reason']}"
        if order.get("delay_reason")
        else ""
    )

    return (
        f"{llm_answer}\n\n"
        f"---\n\n"
        f"### Order details — {tracking}\n\n"
        f"- **Status:** {order['status']}\n"
        f"- **Order date:** {order.get('order_date', 'N/A')}\n"
        f"- **Estimated delivery:** {order['estimated_delivery']}\n"
        f"- **Shipping method:** {order.get('shipping_method', 'N/A')}\n"
        f"- **Region:** {order.get('shipping_region', 'N/A')}"
        f"{delay_line}\n\n"
        f"**Items:**\n{items_lines}\n\n"
        f"[Track your order]({order.get('tracking_url', '#')})"
    )


# ── product utilities ─────────────────────────────────────────────────────────


def extract_product_id(text: str) -> str | None:
    """Extract a product ID (e.g. P0001) from user text.

    Args:
        text: Raw user input.

    Returns:
        Uppercase product ID string, or None if not found.
    """
    match = re.search(r"\bP\d{4}\b", text, re.IGNORECASE)
    if match:
        return match.group(0).upper()
    return None
