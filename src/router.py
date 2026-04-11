def detect_intent(text: str) -> str:
    text = text.lower()

    if "order" in text or "pedido" in text or "tracking" in text:
        return "order_status"

    if "return" in text or "devol" in text or "refund" in text:
        return "return_policy"

    if "complaint" in text or "queja" in text:
        return "human"

    return "general"