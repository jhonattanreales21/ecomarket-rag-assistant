from ollama import Client

MODEL_NAME = "gemma2:2b"

client = Client(host="http://127.0.0.1:11434")


def generate_with_gemma(prompt: str) -> str:
    try:
        response = client.generate(
            model=MODEL_NAME,
            prompt=prompt,
            options={
                "temperature": 0,
                "num_predict": 220
            }
        )
        return response["response"].strip()

    except Exception as e:
        return f"Error while calling Gemma 2B: {e}"