import streamlit as st

from src.router import detect_intent
from src.order_service import get_order
from src.returns_service import load_policy
from src.prompts import (
    build_order_prompt,
    build_return_prompt,
    build_human_prompt,
    build_general_prompt,
)
from src.llm_client import generate_with_gemma

st.set_page_config(page_title="EcoMarket Support Assistant", page_icon="🛍️")
st.title("EcoMarket Support Assistant")
st.caption("Prototype for customer support automation in EcoMarket")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_intent" not in st.session_state:
    st.session_state.last_intent = "None"

with st.sidebar:
    st.subheader("System Info")
    st.write(f"Detected intent: **{st.session_state.last_intent}**")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Ask your question...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    intent = detect_intent(user_input)
    st.session_state.last_intent = intent

    with st.spinner("Generating response..."):
        if intent == "order_status":
            words = user_input.split()
            tracking = None

            for w in words:
                clean_word = w.strip(".,!?;:()[]{}\"'")
                if "eco" in clean_word.lower():
                    tracking = clean_word

            if tracking:
                order = get_order(tracking)

                if order:
                    prompt = build_order_prompt(order, user_input)
                    generated_answer = generate_with_gemma(prompt)

                    answer = f"""
{generated_answer}

---

### 📦 Order details

- **Order number:** {tracking}  
- **Status:** {order['status']}  
- **Estimated delivery:** {order['estimated_delivery']}  

🔗 [Track your order]({order['tracking_url']})
"""
                else:
                    answer = (
                        "I could not find that order in the sample database. "
                        "Please verify the tracking number and try again."
                    )
            else:
                answer = "Please provide a tracking number, for example: **ECO1001**."

        elif intent == "return_policy":
            policy = load_policy()
            prompt = build_return_prompt(policy, user_input)
            answer = generate_with_gemma(prompt)

        elif intent == "human":
            prompt = build_human_prompt(user_input)
            answer = generate_with_gemma(prompt)

        else:
            prompt = build_general_prompt(user_input)
            answer = generate_with_gemma(prompt)

    st.session_state.messages.append({"role": "assistant", "content": answer})

    with st.chat_message("assistant"):
        st.markdown(answer)