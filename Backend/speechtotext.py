# Backend/speechtotext.py
"""
Speech-to-text via sounddevice recording + SpeechRecognition's Google
Web Speech API backend. Supports one-shot and continuous listening.
"""

import io
import time
import threading
from pathlib import Path

import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wav
import speech_recognition as sr
from dotenv import dotenv_values

BASE_DIR = Path(__file__).resolve().parent
env_vars = dotenv_values(BASE_DIR.parent / ".env")

try:
    MicrophoneIndex = int(env_vars.get("MicrophoneIndex", 0))
except (TypeError, ValueError):
    MicrophoneIndex = None  # use system default device


class SpeechToText:
    def __init__(self, samplerate: int = 44100, channels: int = 1, record_seconds: int = 5):
        self.recognizer = sr.Recognizer()
        self.is_listening = False
        self.listen_thread: threading.Thread | None = None
        self.samplerate = samplerate
        self.channels = channels
        self.dtype = "int16"
        self.record_seconds = record_seconds

        try:
            sd.query_devices()
            self.microphone_available = True
            print("[Voice] Microphone initialized (via sounddevice).")
        except Exception as e:
            print(f"[Error] initializing microphone: {e}")
            self.microphone_available = False

    @property
    def microphone(self) -> bool:
        return self.microphone_available

    def _record_clip(self) -> sr.AudioData | None:
        """Record one clip and return it as SpeechRecognition AudioData."""
        try:
            recording = sd.rec(
                int(self.record_seconds * self.samplerate),
                samplerate=self.samplerate,
                channels=self.channels,
                dtype=self.dtype,
                device=MicrophoneIndex,
            )
            sd.wait()

            buf = io.BytesIO()
            wav.write(buf, self.samplerate, recording)
            buf.seek(0)

            with sr.AudioFile(buf) as source:
                return self.recognizer.record(source)
        except Exception as e:
            print(f"[Error] recording audio: {e}")
            return None

    def listen_continuously(self, callback) -> None:
        if not self.microphone_available:
            print("[Error] No microphone available.")
            return

        def loop():
            while self.is_listening:
                audio = self._record_clip()
                if audio is None:
                    time.sleep(0.5)
                    continue
                try:
                    text = self.recognizer.recognize_google(audio)
                    if text and text.strip():
                        print(f"[Voice] Recognized: {text}")
                        callback(text)
                except sr.UnknownValueError:
                    pass  # silence / unintelligible — expected, not an error
                except sr.RequestError as e:
                    print(f"[Error] Speech API error: {e}")
                    time.sleep(1)  # back off before retrying on network errors

        self.listen_thread = threading.Thread(target=loop, daemon=True)
        self.listen_thread.start()

    def start_listening(self, callback) -> None:
        if self.is_listening:
            return
        self.is_listening = True
        self.listen_continuously(callback)
        print("[Voice] Started continuous listening...")

    def stop_listening(self) -> None:
        self.is_listening = False
        if self.listen_thread:
            self.listen_thread.join(timeout=self.record_seconds + 2)
            self.listen_thread = None
        print("[Voice] Stopped listening.")

    def listen_once(self) -> str | None:
        if not self.microphone_available:
            print("[Error] No microphone available.")
            return None

        print(f"[Voice] Listening ({self.record_seconds}s)...")
        audio = self._record_clip()
        if audio is None:
            return None

        try:
            print("[Voice] Processing...")
            text = self.recognizer.recognize_google(audio)
            print(f"[Voice] You said: {text}")
            return text
        except sr.UnknownValueError:
            print("[Error] Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"[Error] Speech API error: {e}")
            return None


def get_available_microphones() -> list[str]:
    try:
        return [d["name"] for d in sd.query_devices()]
    except Exception as e:
        print(f"[Error] listing microphones: {e}")
        return []


def test_microphone() -> None:
    print("[Voice] Available microphones:")
    for mic in get_available_microphones():
        print(f"  - {mic}")

    stt = SpeechToText()

    while True:
        print("\nOptions:")
        print("1. Listen once")
        print("2. Start continuous listening")
        print("3. Stop continuous listening")
        print("4. Exit")

        choice = input("Choose option (1-4): ").strip()

        if choice == "1":
            result = stt.listen_once()
            if result:
                print(f"[Voice] You said: {result}")
        elif choice == "2":
            stt.start_listening(lambda text: print(f"[Voice] Continuous: {text}"))
        elif choice == "3":
            stt.stop_listening()
        elif choice == "4":
            stt.stop_listening()
            break
        else:
            print("[Error] Invalid choice.")


if __name__ == "__main__":
    test_microphone()