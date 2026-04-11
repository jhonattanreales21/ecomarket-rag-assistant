def generate_response(prompt: str) -> str:
    # Simulación de LLM (porque el taller permite prompts sin modelo real)
    # Aquí puedes luego conectar Ollama o un LLM real

    if "Delayed" in prompt:
        return (
            "I’m sorry for the delay with your order.\n\n"
            "It is currently marked as **Delayed**, and the estimated delivery date has been updated.\n\n"
            "You can track your order using the link provided.\n\n"
            "Please let me know if you need further assistance."
        )

    if "return policy" in prompt.lower():
        return (
            "You can return eligible products within 30 days if they are unused and in original packaging.\n\n"
            "Please note that perishable goods and hygiene products are not eligible for return.\n\n"
            "If your item arrived damaged, you can report it with evidence for assistance."
        )

    return "Thank you for your question. I’m here to help you."