from ollama import Client

MODEL_NAME = "gemma2:2b"

# Connect to the locally running Ollama server
client = Client(host="http://127.0.0.1:11434")


def generate_llm_response(prompt: str) -> str:
    """Send a prompt to Gemma 2B and return the generated text.

    Temperature 0 ensures deterministic, consistent responses.
    num_predict caps the output length to keep replies concise.
    """
    try:
        response = client.generate(
            model=MODEL_NAME,
            prompt=prompt,
            options={"temperature": 0, "num_predict": 220},
        )
        return response["response"].strip()

    except Exception as e:
        # Surface connection or model errors without crashing the app
        return f"Error while calling {MODEL_NAME}: {e}"
