import json
from pathlib import Path

# Use the enhanced orders dataset (30 realistic orders with full metadata)
ORDERS_PATH = Path("data/orders_enhanced.json")


def load_orders():
    """Load all mock orders from the JSON file."""
    with open(ORDERS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_tracking(text: str) -> str:
    """Strip punctuation and uppercase the tracking number for consistent comparison."""
    return text.strip(".,!?;:()[]{}\"' ").upper()


def get_order(tracking_number: str):
    """Return the order dict matching the given tracking number, or None if not found."""
    normalized = normalize_tracking(tracking_number)
    orders = load_orders()

    for order in orders:
        if normalize_tracking(order["tracking_number"]) == normalized:
            return order

    return None
