# Backend/automation.py
"""
System automation: open/close apps, web/YouTube/Google search shortcuts,
volume/power control, and a lightweight background reminder service.
"""

import os
import sys
import json
import time
import threading
import datetime
import webbrowser
from pathlib import Path

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except Exception as e:
    PYAUTOGUI_AVAILABLE = False
    print(f"[Warning] pyautogui unavailable, system volume keys disabled: {e}")

# Base directory of this file -> used to build OS-correct paths regardless
# of where the script is launched from.
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "Data"
REMINDERS_FILE = DATA_DIR / "reminders.json"

WEBSITES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "facebook": "https://www.facebook.com",
    "instagram": "https://www.instagram.com",
    "twitter": "https://www.twitter.com",
    "x": "https://www.twitter.com",
    "linkedin": "https://www.linkedin.com",
    "github": "https://www.github.com",
    "chatgpt": "https://chat.openai.com",
    "whatsapp": "https://web.whatsapp.com",
}


class AutomationSystem:
    """Executes simple text commands like 'open chrome' or 'system mute'."""

    def execute_command(self, command: str) -> str:
        command = (command or "").strip()
        if not command:
            return "No command given."

        try:
            if command.startswith("open "):
                return self._open(command[len("open "):].strip())

            if command.startswith("close "):
                return self._close(command[len("close "):].strip())

            if command.startswith("play "):
                song = command[len("play "):].strip()
                webbrowser.open(f"https://www.youtube.com/results?search_query={song}")
                return f"Playing {song}..."

            if command.startswith("system "):
                return self._system(command[len("system "):].strip().lower())

            if command.startswith("google "):
                query = command[len("google "):].strip()
                webbrowser.open(f"https://www.google.com/search?q={query}")
                return f"Searching Google for '{query}'..."

            if command.startswith("youtube "):
                query = command[len("youtube "):].strip()
                webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
                return f"Searching YouTube for '{query}'..."

            if command.startswith("reminder "):
                reminder_text = command[len("reminder "):].strip()
                when = add_reminder(reminder_text)
                return f"Reminder set for {when.strftime('%Y-%m-%d %H:%M:%S')}: {reminder_text}"

            return f"Unrecognized command: {command}"

        except Exception as e:
            return f"Error: {e}"

    def _open(self, app: str) -> str:
        if not app:
            return "No app or website specified."
        app_key = app.lower()

        if app_key in WEBSITES:
            webbrowser.open(WEBSITES[app_key])
            return f"Opening {app}..."

        # Looks like a URL already
        if app_key.startswith("http://") or app_key.startswith("https://"):
            webbrowser.open(app)
            return f"Opening {app}..."

        try:
            from AppOpener import open as open_app
            open_app(app, match_closest=True, output=False)
            return f"Opening {app}..."
        except Exception:
            pass

        # Platform-aware fallback launch
        try:
            if sys.platform.startswith("win"):
                os.startfile(app)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                os.system(f"open -a '{app}'")
            else:
                os.system(f"{app} &")
            return f"Attempting to open {app}..."
        except Exception as e:
            return f"Could not open {app}: {e}"

    def _close(self, app: str) -> str:
        if not app:
            return "No app specified to close."
        try:
            if sys.platform.startswith("win"):
                os.system(f'taskkill /f /im "{app}.exe"')
            else:
                os.system(f"pkill -f '{app}'")
            return f"Closing {app}..."
        except Exception as e:
            return f"Could not close {app}: {e}"

    def _system(self, action: str) -> str:
        if action == "mute":
            if PYAUTOGUI_AVAILABLE:
                pyautogui.press("volumemute")
                return "Muted."
            return "Volume control unavailable on this system."
        if action == "volume up":
            if PYAUTOGUI_AVAILABLE:
                pyautogui.press("volumeup")
                return "Volume up."
            return "Volume control unavailable on this system."
        if action == "volume down":
            if PYAUTOGUI_AVAILABLE:
                pyautogui.press("volumedown")
                return "Volume down."
            return "Volume control unavailable on this system."
        if action == "shutdown":
            if sys.platform.startswith("win"):
                os.system("shutdown /s /t 1")
            else:
                os.system("shutdown -h now")
            return "Shutting down..."
        if action == "restart":
            if sys.platform.startswith("win"):
                os.system("shutdown /r /t 1")
            else:
                os.system("shutdown -r now")
            return "Restarting..."
        return f"Unknown system command: {action}"


# ----------------------------------------------------------------------
# Reminder functionality
# ----------------------------------------------------------------------

_reminders_lock = threading.Lock()
reminders: list[tuple[str, datetime.datetime]] = []


def load_reminders() -> None:
    global reminders
    with _reminders_lock:
        reminders = []
        if not REMINDERS_FILE.exists():
            return
        try:
            with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for text, time_str in data:
                try:
                    reminders.append((text, datetime.datetime.fromisoformat(time_str)))
                except ValueError:
                    continue  # skip malformed entries instead of crashing
        except (json.JSONDecodeError, OSError) as e:
            print(f"[Warning] Could not load reminders, starting fresh: {e}")
            reminders = []


def save_reminders() -> None:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with _reminders_lock:
            data = [[text, dt.isoformat()] for text, dt in reminders]
        with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except OSError as e:
        print(f"[Error] saving reminders: {e}")


def _parse_reminder_time(text: str, now: datetime.datetime) -> datetime.datetime:
    """Best-effort parse of 'in N minutes/hours/seconds'; otherwise default delay."""
    import re

    m = re.search(r"\bin\s+(\d+)\s*(second|sec|minute|min|hour|hr)s?\b", text, re.IGNORECASE)
    if m:
        amount = int(m.group(1))
        unit = m.group(2).lower()
        if unit.startswith("sec"):
            return now + datetime.timedelta(seconds=amount)
        if unit.startswith("min"):
            return now + datetime.timedelta(minutes=amount)
        if unit.startswith("hour") or unit.startswith("hr"):
            return now + datetime.timedelta(hours=amount)

    # Fall back to a short default delay so the reminder is still useful/testable
    return now + datetime.timedelta(minutes=1)


def add_reminder(text: str) -> datetime.datetime:
    now = datetime.datetime.now()
    reminder_time = _parse_reminder_time(text, now)

    with _reminders_lock:
        reminders.append((text, reminder_time))
    save_reminders()
    print(f"[Reminder] Added for {reminder_time.strftime('%H:%M:%S')}: {text}")
    return reminder_time


def check_reminders(poll_seconds: float = 5.0) -> None:
    load_reminders()
    while True:
        now = datetime.datetime.now()
        fired = []
        with _reminders_lock:
            still_pending = []
            for message, remind_time in reminders:
                if now >= remind_time:
                    fired.append(message)
                else:
                    still_pending.append((message, remind_time))
            reminders[:] = still_pending

        for message in fired:
            print(f"\n[Reminder]: {message}")

        if fired:
            save_reminders()

        time.sleep(poll_seconds)


def start_reminder_checker() -> threading.Thread:
    thread = threading.Thread(target=check_reminders, daemon=True)
    thread.start()
    return thread