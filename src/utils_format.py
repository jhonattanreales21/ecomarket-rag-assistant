def format_order_response(llm_answer: str, tracking: str, order: dict) -> str:
    """Combine the LLM's reply with a structured order details card."""
    return (
        f"{llm_answer}\n\n"
        f"---\n\n"
        f"### 📦 Order details\n\n"
        f"- **Order number:** {tracking}\n"
        f"- **Status:** {order['status']}\n"
        f"- **Estimated delivery:** {order['estimated_delivery']}\n\n"
        f"🔗 [Track your order]({order['tracking_url']})\n"
    )
