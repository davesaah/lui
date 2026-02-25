import ollama


def fetch_models() -> list[str]:
    """
    Fetch available Ollama models (excluding embeddings).
    """
    response = ollama.list()

    # Extract the 'model' attribute from each object in the models list and
    # filter out models containing 'embed' if you want to exclude embeddings
    model_names = [
        m.model for m in response.models
        if 'embed' not in m.model
    ]

    return model_names


def stream_response(messages: list, model: str, use_rag: bool):
    stream = ollama.chat(
        model=model,
        messages=messages,  # full message history here
        stream=True,
        options={"temperature": 0.2},
    )

    for chunk in stream:
        yield chunk["message"]["content"]
