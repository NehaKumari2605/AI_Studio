import json
import os
from datetime import datetime


def add_message(history, role, message):
    """
    Add a message to chat history with timestamp.
    """

    if not message.strip():
        return

    history.append(
        {
            "role": role,
            "message": message,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    )


def export_chat(history):
    """
    Convert chat history to JSON format.
    """
    return json.dumps(
        history,
        indent=4,
        ensure_ascii=False
    )


def conversation_stats(history):
    """
    Calculate conversation statistics.
    """

    total_messages = len(history)

    user_messages = len(
        [msg for msg in history if msg["role"] == "user"]
    )

    assistant_messages = len(
        [msg for msg in history if msg["role"] == "assistant"]
    )

    total_words = sum(
        len(msg["message"].split())
        for msg in history
    )

    if history:
        start = datetime.strptime(
            history[0]["timestamp"],
            "%Y-%m-%d %H:%M:%S"
        )

        end = datetime.strptime(
            history[-1]["timestamp"],
            "%Y-%m-%d %H:%M:%S"
        )

        duration = end - start

    else:
        duration = "0:00:00"
    return {
        "Total Messages": total_messages,
        "User Messages": user_messages,
        "AI Messages": assistant_messages,
        "Total Words": total_words,
        "Conversation Duration": str(duration)
    }


def get_last_response(history):
    """
    Return the last assistant response.
    """

    for msg in reversed(history):
        if msg["role"] == "assistant":
            return msg["message"]
 

HISTORY_FILE = "history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)