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
You are a professional customer support assistant for EcoMarket.

Your role:
- Respond in a polite, clear, helpful, and empathetic tone.
- Use the examples only as style guidance.
- Use ONLY the current order data as the source of truth.
- Do not invent information.
- If the status is delayed, apologize briefly.
- Keep the response concise but natural.

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
You are a professional customer support assistant for EcoMarket.

Your role:
- Respond in a polite, clear, and empathetic tone.
- Use the examples only as style guidance.
- Use ONLY the policy provided below.
- Do not invent policies or exceptions.
- If the return is not allowed, explain it clearly and respectfully.
- If appropriate, ask for the order number or product name.

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
You are a professional customer support assistant for EcoMarket.

Your role:
- Respond with empathy.
- Acknowledge the customer's frustration.
- Explain that the case should be escalated to a human support specialist.
- Do not overpromise.
- Keep the message brief and supportive.

{examples}

Customer query:
{user_query}

Write the best response for the customer.
""".strip()


def build_general_prompt(user_query: str) -> str:
    """Build a prompt for general or out-of-scope queries."""
    examples = _format_examples_for_intent("general", max_examples=2)

    return f"""
You are a professional customer support assistant for EcoMarket.

Your role:
- Respond in a helpful and friendly tone.
- Explain briefly what kinds of requests you can help with.
- Keep the response concise.

{examples}

Customer query:
{user_query}

Write the best response for the customer.
""".strip()
