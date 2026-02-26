import ollama
from lib.database import update_session_title


def run(messages, session_id, model):
    """Update chat title with conversation context in the background"""
    try:
        chat_context = "\n".join(
            [f"{m['role']}: {m['content']}" for m in messages])

        response = ollama.chat(
            model=model,
            messages=[{
                "role": "user",
                "content": f"Based on this conversation:\n{chat_context}" +
                "\n\nSuggest a title. Return ONLY the title text. No quotes."
            }]
        )

        generated_title = response['message']['content']

        if session_id:
            update_session_title(session_id, generated_title)
    except Exception as e:
        print(f"Background title generation failed: {e}")
