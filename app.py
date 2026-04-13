import streamlit as st

# Internal modules: routing, data retrieval, prompt builders, and LLM client
from src.router import detect_intent
from src.order_service import get_order
from src.returns_service import load_policy
from src.prompts import (
    build_order_prompt,
    build_return_prompt,
    build_human_prompt,
    build_general_prompt,
)
from src.llm_client import generate_llm_response
from src.utils_format import format_order_response

#  Page config and title
st.set_page_config(page_title="EcoMarket Support Assistant", page_icon="🛍️")
st.title("EcoMarket Support Assistant")
st.caption("Prototype for customer support automation in EcoMarket")

#  Session state: persist chat history and last detected intent across reruns
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_intent" not in st.session_state:
    st.session_state.last_intent = "None"

#  Sidebar: shows which intent was detected for the last message
with st.sidebar:
    st.subheader("System Info")
    st.write(f"Detected intent: **{st.session_state.last_intent}**")

#  Render previous messages on each rerun
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

#  Chat input: blocks until the user submits a message
user_input = st.chat_input("Ask your question...")

if user_input:
    # Save and display the user message immediately
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Classify the user's message into one of four intents
    intent = detect_intent(user_input)
    st.session_state.last_intent = intent

    with st.spinner("Generating response..."):

        if intent == "order_status":
            # Extract the tracking number (any word containing "eco") from the input
            words = user_input.split()
            tracking = None

            for w in words:
                clean_word = w.strip(".,!?;:()[]{}\"'")
                if "eco" in clean_word.lower():
                    tracking = clean_word

            if tracking:
                order = get_order(tracking)  # Look up the order in the mock database

                if order:
                    # Build a prompt with the real order data and let the LLM draft the reply
                    prompt = build_order_prompt(order, user_input)
                    generated_answer = generate_llm_response(prompt)

                    # Append a structured order summary below the LLM's natural-language reply
                    answer = format_order_response(generated_answer, tracking, order)
                else:
                    # Order ID was found in the message but does not exist in the database
                    answer = (
                        "I could not find that order in the sample database. "
                        "Please verify the tracking number and try again."
                    )
            else:
                # No tracking number detected — ask the user to provide one
                answer = "Please provide a tracking number, for example: **ECO1001**."

        elif intent == "return_policy":
            # Load the policy document and inject it into the prompt as the source of truth
            policy = load_policy()
            prompt = build_return_prompt(policy, user_input)
            answer = generate_llm_response(prompt)

        elif intent == "human":
            # Escalation path: the LLM acknowledges frustration and redirects to a human agent
            prompt = build_human_prompt(user_input)
            answer = generate_llm_response(prompt)

        else:
            # Catch-all for general or unrecognised queries
            prompt = build_general_prompt(user_input)
            answer = generate_llm_response(prompt)

    # Save and display the assistant's reply
    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)
