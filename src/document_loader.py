"""Document loading pipeline for EcoMarket RAG system.

Loads PDFs, Excel files, and JSON files from the data/ directory
and converts them into LangChain Document objects ready for chunking
and indexing.
"""

import json
from pathlib import Path
from typing import List

import pandas as pd
from langchain_core.documents import Document
from pypdf import PdfReader

# ── paths ──────────────────────────────────────────────────────────────────
DATA_DIR = Path("data")

RETURNS_POLICY_PDF = DATA_DIR / "EcoMarket ReturnPolicy.pdf"
SHIPPING_POLICY_PDF = DATA_DIR / "EcoMarket ShippingPolicy.pdf"
INVENTORY_XLSX = DATA_DIR / "inventory_200_products_named.xlsx"
PRODUCT_CATALOG_XLSX = DATA_DIR / "product_catalog.xlsx"
ORDERS_JSON = DATA_DIR / "orders_enhanced.json"
SUPPORT_EXAMPLES_JSON = DATA_DIR / "support_examples_enhanced.json"


# ── PDF loaders ─────────────────────────────────────────────────────────────


def _load_pdf(path: Path, doc_type: str) -> List[Document]:
    """Load a PDF file page by page and return a list of Documents.

    Args:
        path: Filesystem path to the PDF.
        doc_type: Metadata tag (e.g. 'returns_policy', 'shipping_policy').

    Returns:
        One Document per PDF page with page-level metadata.
    """
    if not path.exists():
        print(f"[document_loader] WARNING: {path} not found — skipping.")
        return []

    reader = PdfReader(str(path))
    docs: List[Document] = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            docs.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": str(path),
                        "doc_type": doc_type,
                        "page": i + 1,
                    },
                )
            )
    return docs


def load_returns_policy() -> List[Document]:
    """Load the extended return policy PDF."""
    return _load_pdf(RETURNS_POLICY_PDF, "returns_policy")


def load_shipping_policy() -> List[Document]:
    """Load the shipping policy PDF."""
    return _load_pdf(SHIPPING_POLICY_PDF, "shipping_policy")


# ── Excel loaders ────────────────────────────────────────────────────────────


def load_inventory() -> List[Document]:
    """Load inventory Excel file and convert each row to a Document.

    Returns:
        One Document per product row with structured metadata.
    """
    if not INVENTORY_XLSX.exists():
        print(f"[document_loader] WARNING: {INVENTORY_XLSX} not found — skipping.")
        return []

    df = pd.read_excel(INVENTORY_XLSX, dtype=str)
    df.fillna("N/A", inplace=True)
    docs: List[Document] = []

    for _, row in df.iterrows():
        fields = row.to_dict()
        # Build a human-readable sentence from the row for embedding
        text_parts = [f"{k}: {v}" for k, v in fields.items()]
        text = "Inventory record — " + " | ".join(text_parts)

        # Extract key metadata columns (fall back gracefully if missing)
        product_id = fields.get(
            "product_id", fields.get("Product ID", fields.get("Product_ID", "unknown"))
        )
        product_name = fields.get(
            "product_name",
            fields.get("Product Name", fields.get("Product_Name", "unknown")),
        )
        category = fields.get(
            "category", fields.get("Category", fields.get("Category_Name", "unknown"))
        )

        docs.append(
            Document(
                page_content=text,
                metadata={
                    "source": str(INVENTORY_XLSX),
                    "doc_type": "inventory",
                    "product_id": product_id,
                    "product_name": product_name,
                    "category": category,
                },
            )
        )
    return docs


def load_product_catalog() -> List[Document]:
    """Load product catalog Excel and convert each row to a Document.

    Returns:
        One Document per product with description and metadata.
    """
    if not PRODUCT_CATALOG_XLSX.exists():
        print(
            f"[document_loader] WARNING: {PRODUCT_CATALOG_XLSX} not found — skipping."
        )
        return []

    df = pd.read_excel(PRODUCT_CATALOG_XLSX, dtype=str)
    df.fillna("N/A", inplace=True)
    docs: List[Document] = []

    for _, row in df.iterrows():
        fields = row.to_dict()
        text_parts = [f"{k}: {v}" for k, v in fields.items()]
        text = "Product catalog entry — " + " | ".join(text_parts)

        product_id = fields.get(
            "product_id", fields.get("Product ID", fields.get("Product_ID", "unknown"))
        )
        product_name = fields.get(
            "product_name",
            fields.get("Product Name", fields.get("Product_Name", "unknown")),
        )
        category = fields.get(
            "category", fields.get("Category", fields.get("Category_Name", "unknown"))
        )

        docs.append(
            Document(
                page_content=text,
                metadata={
                    "source": str(PRODUCT_CATALOG_XLSX),
                    "doc_type": "product_catalog",
                    "product_id": product_id,
                    "product_name": product_name,
                    "category": category,
                },
            )
        )
    return docs


# ── JSON loaders ─────────────────────────────────────────────────────────────


def load_orders_as_docs() -> List[Document]:
    """Load orders_enhanced.json and convert each order to a Document.

    Returns:
        One Document per order with tracking metadata.
    """
    if not ORDERS_JSON.exists():
        print(f"[document_loader] WARNING: {ORDERS_JSON} not found — skipping.")
        return []

    with open(ORDERS_JSON, "r", encoding="utf-8") as f:
        orders = json.load(f)

    docs: List[Document] = []
    for order in orders:
        tracking = order.get("tracking_number", "unknown")
        status = order.get("status", "unknown")
        est_delivery = order.get("estimated_delivery", "unknown")
        method = order.get("shipping_method", "unknown")
        region = order.get("shipping_region", "unknown")
        order_date = order.get("order_date", "unknown")
        delay_reason = order.get("delay_reason", "N/A")

        items = order.get("items", [])
        items_text = "; ".join(
            f"{it.get('product_name', '?')} (qty {it.get('quantity', '?')}, "
            f"perishable: {it.get('perishable', '?')})"
            for it in items
        )

        text = (
            f"Order {tracking} — Status: {status} | "
            f"Order date: {order_date} | "
            f"Estimated delivery: {est_delivery} | "
            f"Shipping method: {method} | "
            f"Region: {region} | "
            f"Delay reason: {delay_reason} | "
            f"Items: {items_text}"
        )

        docs.append(
            Document(
                page_content=text,
                metadata={
                    "source": str(ORDERS_JSON),
                    "doc_type": "order",
                    "tracking_number": tracking,
                    "status": status,
                },
            )
        )
    return docs


def load_support_examples() -> List[Document]:
    """Load support_examples_enhanced.json and convert each example to a Document.

    Returns:
        One Document per example, tagged with intent metadata.
    """
    if not SUPPORT_EXAMPLES_JSON.exists():
        print(
            f"[document_loader] WARNING: {SUPPORT_EXAMPLES_JSON} not found — skipping."
        )
        return []

    with open(SUPPORT_EXAMPLES_JSON, "r", encoding="utf-8") as f:
        examples = json.load(f)

    docs: List[Document] = []
    for ex in examples:
        intent = ex.get("intent", "general")
        query = ex.get("customer_query", "")
        response = ex.get("assistant_response", "")
        context_str = json.dumps(ex.get("context", {}), ensure_ascii=False)

        text = (
            f"Support example [{intent}]\n"
            f"Customer: {query}\n"
            f"Context: {context_str}\n"
            f"Assistant: {response}"
        )

        docs.append(
            Document(
                page_content=text,
                metadata={
                    "source": str(SUPPORT_EXAMPLES_JSON),
                    "doc_type": "support_example",
                    "intent": intent,
                    "example_id": ex.get("id", "unknown"),
                },
            )
        )
    return docs


# ── aggregated loader ────────────────────────────────────────────────────────


def load_all_documents() -> List[Document]:
    """Load all knowledge-base documents from every source.

    Returns:
        Combined list of Documents from PDFs, Excel files, and JSON files.
    """
    all_docs: List[Document] = []

    loaders = [
        ("returns_policy", load_returns_policy),
        ("shipping_policy", load_shipping_policy),
        ("inventory", load_inventory),
        ("product_catalog", load_product_catalog),
        ("orders", load_orders_as_docs),
        ("support_examples", load_support_examples),
    ]

    for name, loader in loaders:
        docs = loader()
        print(f"[document_loader] {name}: {len(docs)} documents loaded.")
        all_docs.extend(docs)

    print(f"[document_loader] Total: {len(all_docs)} documents loaded.")
    return all_docs
