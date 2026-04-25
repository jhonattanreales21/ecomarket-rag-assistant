# Keyword sets that trigger each intent.
# More specific checks run first; fallback is 'general'.

ORDER_KEYWORDS = {
    "order",
    "pedido",
    "tracking",
    "shipment",
    "package",
    "delivery",
    "eco201",
    "where is my",
}

RETURN_KEYWORDS = {
    "return",
    "devol",
    "refund",
    "reembolso",
    "exchange",
    "money back",
    "send back",
}

SHIPPING_KEYWORDS = {
    "shipping",
    "ship",
    "envio",
    "envío",
    "freight",
    "carrier",
    "dispatch",
    "international",
    "express",
    "standard shipping",
    "delivery time",
    "how long",
    "free shipping",
}

PRODUCT_KEYWORDS = {
    "product",
    "item",
    "catalog",
    "ingredient",
    "organic",
    "sustainable",
    "eco-friendly",
    "material",
    "bamboo",
    "milk",
    "beef",
    "soap",
    "bread",
    "protein",
}

INVENTORY_KEYWORDS = {
    "stock",
    "available",
    "availability",
    "inventory",
    "in stock",
    "out of stock",
    "perishable",
    "expire",
    "expiration",
    "shelf life",
    "manufacturing",
    "warehouse",
    "batch",
    "p00",
}

HUMAN_KEYWORDS = {
    "complaint",
    "queja",
    "upset",
    "angry",
    "frustrated",
    "unacceptable",
    "terrible",
    "worst",
    "speak to a human",
    "speak to agent",
    "escalate",
    "supervisor",
    "manager",
}


def detect_intent(text: str) -> str:
    """Classify user input into one of seven intents using keyword matching.

    Precedence: human > order_status > return_policy > shipping > inventory > product > general.

    Args:
        text: Raw user message.

    Returns:
        Intent string.
    """
    lowered = text.lower()

    if any(kw in lowered for kw in HUMAN_KEYWORDS):
        return "human"

    if any(kw in lowered for kw in ORDER_KEYWORDS):
        return "order_status"

    if any(kw in lowered for kw in RETURN_KEYWORDS):
        return "return_policy"

    if any(kw in lowered for kw in SHIPPING_KEYWORDS):
        return "shipping"

    if any(kw in lowered for kw in INVENTORY_KEYWORDS):
        return "inventory"

    if any(kw in lowered for kw in PRODUCT_KEYWORDS):
        return "product"

    return "general"
