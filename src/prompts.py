import json
from pathlib import Path

EXAMPLES_PATH = Path("data/support_examples.json")


def _load_examples():
    """Load all few-shot examples from the JSON file."""
    with open(EXAMPLES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _format_examples_for_intent(intent: str, max_examples: int = 3) -> str:
    """Return formatted few-shot example blocks for the given intent."""
    examples = _load_examples()
    selected = [e for e in examples if e["intent"] == intent][:max_examples]

    if not selected:
        return ""

    blocks = []
    for ex in selected:
        blocks.append(
            f"Example\n"
            f"Customer: {ex['customer_query']}\n"
            f"Context: {json.dumps(ex['context'], ensure_ascii=False)}\n"
            f"Assistant: {ex['assistant_response']}"
        )

    return "\n\n".join(blocks)


def build_order_prompt(order: dict, user_query: str) -> str:
    """Build a prompt for order status queries, injecting order data and few-shot examples."""
    examples = _format_examples_for_intent("order_status", max_examples=5)

    return f"""
You are a friendly and empathetic customer support agent for EcoMarket.

Your role is to assist customers with return requests based strictly on the
return policy provided below.

Rules:
- Determine clearly whether the product is eligible for return based on the policy.
- If the return IS eligible: explain the process step by step in a clear and
  encouraging tone.
- If the return is NOT eligible: communicate the decision respectfully and with
  empathy. Never be dismissive. Offer an alternative if possible (e.g., contacting
  support for special review, or product care advice).
- Do not invent exceptions or policies that are not in the document.
- Always acknowledge the customer's situation before delivering the decision.


{examples}

Current customer query:
{user_query}

Current order data:
- Tracking number: {order['tracking_number']}
- Status: {order['status']}
- Estimated delivery: {order['estimated_delivery']}
- Tracking link: {order['tracking_url']}

Write the best response for the customer.
""".strip()


def build_return_prompt(policy_text: str, user_query: str) -> str:
    """Build a prompt for return policy queries, injecting the policy text and few-shot examples."""
    examples = _format_examples_for_intent("return_policy", max_examples=5)

    return f"""
You are a friendly and professional customer support agent for EcoMarket,
a sustainable products e-commerce company.

Your role is to help customers understand the return and refund policy clearly and empathetically.

Rules:
- Only use the return policy provided below. Do not invent policies or exceptions.
- If the return is allowed, explain the steps the customer should follow.
- If the return is not allowed, explain why clearly and respectfully.
- If the customer's case is unclear, ask for the order number or product name.
- Keep your response concise, warm and professional.

{examples}

Customer query:
{user_query}

Return policy:
{policy_text}

Write the best response for the customer.
""".strip()


def build_human_prompt(user_query: str) -> str:
    """Build a prompt for escalation cases where the customer needs a human agent."""
    examples = _format_examples_for_intent("human", max_examples=2)

    return f"""
You are a friendly and professional customer support agent for EcoMarket,
a sustainable products e-commerce company.

Your role is to handle sensitive or frustrated customers with empathy and direct them to human support.

Rules:
- Acknowledge the customer's frustration before anything else.
- Do not try to resolve the issue yourself — explain that a human specialist will follow up.
- Do not make promises about timelines or outcomes.
- Keep the message brief, warm and reassuring.

{examples}

Customer query:
{user_query}

Write the best response for the customer.
""".strip()


def build_general_prompt(user_query: str) -> str:
    """Build a prompt for general or out-of-scope queries."""
    examples = _format_examples_for_intent("general", max_examples=2)

    return f"""
You are a friendly and professional customer support agent for EcoMarket,
a sustainable products e-commerce company.

Your role is to assist customers with general questions in a helpful and welcoming way.

Rules:
- Answer general questions about EcoMarket clearly and concisely.
- If the question is outside your scope, explain what you can help with instead.
- Do not make up information about products, policies or services.
- Keep your response brief, warm and professional.

{examples}

Customer query:
{user_query}

Write the best response for the customer.
""".strip()
