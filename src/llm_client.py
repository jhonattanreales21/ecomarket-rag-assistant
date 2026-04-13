from ollama import Client

MODEL_NAME = "gemma2:2b"

client = Client(host="http://127.0.0.1:11434")


def generate_llm_response(prompt: str) -> str:
    try:
        response = client.generate(
            model=MODEL_NAME,
            prompt=prompt,
            options={"temperature": 0, "num_predict": 220},
        )
        return response["response"].strip()

    except Exception as e:
        return f"Error while calling {MODEL_NAME}: {e}"
