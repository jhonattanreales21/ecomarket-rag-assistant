import json
from pathlib import Path

ORDERS_PATH = Path("data/orders.json")


def load_orders():
    with open(ORDERS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_tracking(text: str) -> str:
    return text.strip(".,!?;:()[]{}\"' ").upper()


def get_order(tracking_number: str):
    normalized = normalize_tracking(tracking_number)
    orders = load_orders()

    for order in orders:
        if normalize_tracking(order["tracking_number"]) == normalized:
            return order
    return None