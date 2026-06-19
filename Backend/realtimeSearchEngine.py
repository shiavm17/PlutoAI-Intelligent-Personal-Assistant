# Backend/realtimeSearchEngine.py
"""
Real-time search-augmented chatbot: pulls fresh Google results and feeds
them to the LLM as context before answering.
"""

import json
import datetime
from pathlib import Path

from groq import Groq
from dotenv import dotenv_values

try:
    from googlesearch import search
except ImportError:
    search = None

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "Data"
CHATLOG_FILE = DATA_DIR / "ChatLog.json"

env_vars = dotenv_values(BASE_DIR.parent / ".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")
GroqAPIKey = env_vars.get("GroqAPIKey")

if not GroqAPIKey:
    print("[Warning] GroqAPIKey not set in .env — RealtimeSearchEngine calls will fail.")

client = None
if GroqAPIKey:
    try:
        client = Groq(api_key=GroqAPIKey)
    except Exception as e:
        print(f"[Warning] Failed to initialize Groq client: {e}")

System = f"""Hello, I am {Username}. You are a very accurate and advanced AI chatbot named {Assistantname}, which has real-time up-to-date information from the internet.
*** Provide answers in a professional way. Make sure to add full stops, commas, question marks, and use proper grammar.***
*** Just answer the question from the provided data in a professional way. ***"""

BASE_SYSTEM_CHATBOT = [
    {"role": "system", "content": System},
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello, how can I help you?"},
]


def _ensure_chatlog() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not CHATLOG_FILE.exists():
        with open(CHATLOG_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


def _load_messages() -> list:
    _ensure_chatlog()
    try:
        with open(CHATLOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"[Warning] ChatLog.json was unreadable, starting fresh: {e}")
        return []


def _save_messages(messages: list) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(CHATLOG_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=4)


_ensure_chatlog()


def GoogleSearch(query: str) -> str:
    if search is None:
        return f"[Search unavailable: 'googlesearch' package not installed]\nQuery: {query}"

    try:
        results = list(search(query, advanced=True, num_results=5))
    except Exception as e:
        return f"[Search failed for '{query}': {e}]"

    if not results:
        return f"No search results found for '{query}'."

    lines = [f"The search results for '{query}' are:", "[start]"]
    for r in results:
        title = getattr(r, "title", "") or "(no title)"
        description = getattr(r, "description", "") or ""
        lines.append(f"Title: {title}\nDescription: {description}\n")
    lines.append("[end]")
    return "\n".join(lines)


def AnswerModifier(Answer: str) -> str:
    lines = [line for line in Answer.split("\n") if line.strip()]
    return "\n".join(lines)


def Information() -> str:
    now = datetime.datetime.now()
    return (
        "Use this real-time information if needed:\n"
        f"Day: {now.strftime('%A')}\n"
        f"Date: {now.strftime('%d')}\n"
        f"Month: {now.strftime('%B')}\n"
        f"Year: {now.strftime('%Y')}\n"
        f"Time: {now.strftime('%H')} hours, {now.strftime('%M')} minutes, {now.strftime('%S')} seconds.\n"
    )


def RealtimeSearchEngine(Query: str) -> str:
    global client
    if not client:
        if GroqAPIKey:
            try:
                client = Groq(api_key=GroqAPIKey)
            except Exception as e:
                return f"I apologize, but I could not initialize the Chat model: {e}"
        else:
            return "I can't reach the chat model right now — GroqAPIKey is missing from .env."

    messages = _load_messages()
    messages.append({"role": "user", "content": str(Query)})

    # Build a fresh system-message list each call instead of mutating a
    # shared module-level list (the original appended to SystemChatBot on
    # every call without ever popping the matching entry on error paths,
    # causing it to grow unbounded).
    system_chatbot = list(BASE_SYSTEM_CHATBOT) + [
        {"role": "system", "content": GoogleSearch(Query)}
    ]

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=system_chatbot + [{"role": "system", "content": Information()}] + messages,
            temperature=0.7,
            max_tokens=2048,
            top_p=1,
            stream=True,
            stop=None,
        )

        answer = ""
        for chunk in completion:
            delta = chunk.choices[0].delta.content
            if delta:
                answer += delta

        answer = answer.strip().replace("</s>", "")
        messages.append({"role": "assistant", "content": answer})
        _save_messages(messages)

        return AnswerModifier(answer)

    except Exception as e:
        print(f"[Error] RealtimeSearchEngine: {e}")
        return "I apologize, but I encountered an error while searching for that. Please try again later."


if __name__ == "__main__":
    while True:
        try:
            prompt = input("Enter your query: ")
        except (EOFError, KeyboardInterrupt):
            break
        if prompt.strip().lower() in {"exit", "quit"}:
            break
        print(RealtimeSearchEngine(prompt))