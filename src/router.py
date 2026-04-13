# Keyword sets that trigger each intent — order matters: more specific checks run first
ORDER_KEYWORDS = {"order", "pedido", "tracking"}
RETURN_KEYWORDS = {"return", "devol", "refund"}
HUMAN_KEYWORDS = {"complaint", "queja"}


def detect_intent(text: str) -> str:
    """Classify user input into one of four intents using keyword matching."""
    text = text.lower()

    if any(kw in text for kw in ORDER_KEYWORDS):
        return "order_status"

    if any(kw in text for kw in RETURN_KEYWORDS):
        return "return_policy"

    if any(kw in text for kw in HUMAN_KEYWORDS):
        return "human"

    # Default: no specific intent detected
    return "general"
