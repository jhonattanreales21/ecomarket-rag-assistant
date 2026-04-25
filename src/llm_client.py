"""LLM client: thin wrapper around Ollama for Gemma 2B generation.

Provides a single generate function with structured error handling for
the most common failure modes (server not running, model not pulled).
"""

from ollama import Client, ResponseError

MODEL_NAME = "gemma2:2b"
OLLAMA_HOST = "http://127.0.0.1:11434"

# Connect to the locally running Ollama server
client = Client(host=OLLAMA_HOST)


def generate_llm_response(prompt: str, max_tokens: int = 350) -> str:
    """Send a prompt to Gemma 2B and return the generated text.

    Temperature 0 ensures deterministic, factual responses.
    max_tokens caps output length — increase for longer RAG answers.

    Args:
        prompt: The complete prompt string to send to the model.
        max_tokens: Maximum number of tokens in the generated response.

    Returns:
        Generated response text, or a user-friendly error message.
    """
    try:
        response = client.generate(
            model=MODEL_NAME,
            prompt=prompt,
            options={"temperature": 0, "num_predict": max_tokens},
        )
        return response["response"].strip()

    except ResponseError as e:
        if "model" in str(e).lower() and "not found" in str(e).lower():
            return (
                f"The AI model '{MODEL_NAME}' is not available. "
                f"Please run: `ollama pull {MODEL_NAME}` and try again."
            )
        return f"Ollama API error: {e}"

    except ConnectionError:
        return (
            "Could not connect to the Ollama server. "
            "Please start it with: `ollama serve`"
        )

    except Exception as e:
        error_str = str(e).lower()
        if "connection" in error_str or "refused" in error_str:
            return (
                "Could not connect to the Ollama server. "
                "Please start it with: `ollama serve`"
            )
        return f"Unexpected error while calling {MODEL_NAME}: {e}"
