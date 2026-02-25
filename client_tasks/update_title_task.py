import ollama
from lib.database import update_session_title


def run(messages, session_id, model):
    """Function to run in a separate thread."""
    try:
        chat_context = "\n".join(
            [f"{m['role']}: {m['content']}" for m in messages])

        # This call happens in the background
        res = ollama.chat(
            model=model,
            messages=[{
                "role": "user",
                "content": f"Based on this conversation:\n{chat_context}\n\nSuggest a title. Return ONLY the title text. No quotes."
            }]
        )

        generated_title = res['message']['content'].strip().split('\n')[
            0].replace('"', '')

        # Update database directly
        if session_id:
            update_session_title(session_id, generated_title)
            # Note: We don't use st.toast here because it's not thread-safe
    except Exception as e:
        print(f"Background title generation failed: {e}")
