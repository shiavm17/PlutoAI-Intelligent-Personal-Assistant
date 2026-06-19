# Backend/chatbot.py
"""
General-purpose conversational chatbot backed by Groq, with a persisted
chat log and basic real-time context injection (date/time).
"""

import json
import datetime
from pathlib import Path

from groq import Groq
from dotenv import dotenv_values

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "Data"
CHATLOG_FILE = DATA_DIR / "ChatLog.json"

env_vars = dotenv_values(BASE_DIR.parent / ".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")
GroqAPIKey = env_vars.get("GroqAPIKey")

if not GroqAPIKey:
    print("[Warning] GroqAPIKey not set in .env — ChatBot calls will fail.")

client = None
if GroqAPIKey:
    try:
        client = Groq(api_key=GroqAPIKey)
    except Exception as e:
        print(f"[Warning] Failed to initialize Groq client: {e}")

System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which also has real-time up-to-date information from the internet.
*** Do not tell time until I ask, do not talk too much, just answer the question.***
*** Reply in only English, even if the question is in Hindi, reply in English.***
*** Do not provide notes in the output, just answer the question and never mention your training data. ***
"""

SystemChatBot = [{"role": "system", "content": System}]


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


def RealtimeInformation() -> str:
    now = datetime.datetime.now()
    return (
        "Please use this real-time information if needed,\n"
        f"Day: {now.strftime('%A')}\n"
        f"Date: {now.strftime('%d')}\n"
        f"Month: {now.strftime('%B')}\n"
        f"Year: {now.strftime('%Y')}\n"
        f"Time: {now.strftime('%H')} hour :{now.strftime('%M')} minute :{now.strftime('%S')} seconds.\n"
    )


def AnswerModifier(Answer: str) -> str:
    lines = [line for line in Answer.split("\n") if line.strip()]
    return "\n".join(lines)


def ChatBot(Query: str, model_name: str = "llama-3.3-70b-versatile") -> str:
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

    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=SystemChatBot + [{"role": "system", "content": RealtimeInformation()}] + messages,
            max_tokens=1024,
            temperature=0.7,
            top_p=1,
            stream=True,
            stop=None,
        )

        answer = ""
        for chunk in completion:
            delta = chunk.choices[0].delta.content
            if delta:
                answer += delta

        answer = answer.replace("</s>", "").replace("</s", "")

        messages.append({"role": "assistant", "content": answer})
        _save_messages(messages)

        return AnswerModifier(answer)

    except Exception as e:
        print(f"[Error] ChatBot: {e}")
        # Don't wipe the user's history on a transient API error — just report it.
        return "I apologize, but I encountered an error while processing your request. Please check your API key or try again later."


if __name__ == "__main__":
    while True:
        try:
            user_input = input("Enter Your Question: ")
        except (EOFError, KeyboardInterrupt):
            break
        if user_input.strip().lower() in {"exit", "quit"}:
            break
        print(ChatBot(user_input))