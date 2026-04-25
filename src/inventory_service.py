"""Inventory service: structured lookups against the product inventory Excel.

Handles product availability, perishability, expiration dates, and
stock queries without relying on the LLM to interpret structured data.
"""

from pathlib import Path
from typing import Optional

import pandas as pd

INVENTORY_PATH = Path("data/inventory_200_products_named.xlsx")

# Cached dataframe — loaded once per process
_inventory_df: Optional[pd.DataFrame] = None


def _load_inventory() -> pd.DataFrame:
    """Load and cache the inventory dataframe.

    Returns:
        Inventory DataFrame with all columns as strings.
    """
    global _inventory_df
    if _inventory_df is None:
        if not INVENTORY_PATH.exists():
            raise FileNotFoundError(
                f"Inventory file not found: {INVENTORY_PATH}. "
                "Please add inventory_200_products_named.xlsx to the data/ folder."
            )
        _inventory_df = pd.read_excel(INVENTORY_PATH, dtype=str)
        _inventory_df.fillna("N/A", inplace=True)
        # Normalize column names: strip whitespace, lowercase
        _inventory_df.columns = [
            c.strip().lower().replace(" ", "_") for c in _inventory_df.columns
        ]
    return _inventory_df


def _normalize(text: str) -> str:
    """Lowercase and strip a string for case-insensitive matching."""
    return text.strip().lower()


def get_product_by_id(product_id: str) -> Optional[dict]:
    """Look up a product by its product_id (e.g. 'P0001').

    Args:
        product_id: Product identifier string.

    Returns:
        Dict of product fields if found, None otherwise.
    """
    df = _load_inventory()
    # Try common column name variants
    id_col = next((c for c in df.columns if "product_id" in c or c == "id"), None)
    if id_col is None:
        return None

    match = df[df[id_col].str.strip().str.upper() == product_id.strip().upper()]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


def get_products_by_name(name: str) -> list[dict]:
    """Search for products whose name contains the given string (case-insensitive).

    Args:
        name: Partial or full product name.

    Returns:
        List of matching product dicts (may be empty).
    """
    df = _load_inventory()
    name_col = next((c for c in df.columns if "product_name" in c or "name" in c), None)
    if name_col is None:
        return []

    mask = df[name_col].str.lower().str.contains(_normalize(name), na=False)
    return df[mask].to_dict(orient="records")


def format_product_summary(product: dict) -> str:
    """Build a human-readable summary string from a product dict.

    Args:
        product: Product row dict from the inventory.

    Returns:
        Formatted multi-line string with key product facts.
    """
    lines = []
    label_map = {
        "product_id": "Product ID",
        "product_name": "Product Name",
        "category": "Category",
        "batch": "Batch",
        "perishable": "Perishable",
        "manufacture_date": "Manufacturing Date",
        "expiration_date": "Expiration Date",
        "shelf_life_days": "Shelf Life",
        "stock_quantity": "Stock",
        "warehouse_location": "Warehouse",
    }
    for key, label in label_map.items():
        value = product.get(key, product.get(label.lower().replace(" ", "_"), "N/A"))
        lines.append(f"- **{label}:** {value}")

    # Include any extra columns not in the map
    for k, v in product.items():
        if k not in label_map:
            lines.append(f"- **{k}:** {v}")

    return "\n".join(lines)
