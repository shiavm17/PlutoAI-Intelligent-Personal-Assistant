# Backend/speechtotext.py
"""
Speech-to-text via Sarwam AI (primary) or Google Web Speech API (fallback).
Supports one-shot and continuous listening.
"""

import io
import time
import threading
from pathlib import Path
from typing import Optional, Callable

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

SarwamAPIKey = env_vars.get("SarwamAPIKey", "")
USE_SARWAM = SarwamAPIKey.strip() != ""

# Import Sarwam AI if available
try:
    from sarwamAI import SarwamSTT, initialize_sarwam
    SARWAM_AVAILABLE = True
except ImportError:
    SARWAM_AVAILABLE = False
    print("[Warning] Sarwam AI module not available. Using fallback (Google Web Speech API).")

# Initialize Sarwam if available
sarwam_stt = None
if USE_SARWAM and SARWAM_AVAILABLE:
    try:
        initialize_sarwam()
        sarwam_stt = SarwamSTT()
    except Exception as e:
        print(f"[Warning] Failed to initialize Sarwam STT: {e}")
        SARWAM_AVAILABLE = False


class SpeechToText:
    def __init__(self, samplerate: int = 44100, channels: int = 1, record_seconds: int = 5):
        self.recognizer = sr.Recognizer()
        self.is_listening = False
        self.listen_thread: Optional[threading.Thread] = None
        self.samplerate = samplerate
        self.channels = channels
        self.dtype = "int16"
        self.record_seconds = record_seconds

        try:
            sd.query_devices()
            self.microphone_available = True
            print("[Voice] Microphone initialized")
        except Exception as e:
            print(f"[Error] initializing microphone: {e}")
            self.microphone_available = False

    @property
    def microphone(self) -> bool:
        return self.microphone_available

    def _record_clip(self) -> Optional[sr.AudioData]:
        """Record one clip and return it as SpeechRecognition AudioData or bytes."""
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

            # Return both formats for flexibility
            with sr.AudioFile(buf) as source:
                audio_data = self.recognizer.record(source)
            
            # Also return raw bytes for Sarwam
            buf.seek(0)
            raw_bytes = buf.read()
            
            return (audio_data, raw_bytes)
        except Exception as e:
            print(f"[Error] recording audio: {e}")
            return None

    def _recognize_with_sarwam(self, audio_bytes: bytes) -> Optional[str]:
        """Recognize speech using Sarwam AI"""
        if not SARWAM_AVAILABLE or not sarwam_stt:
            return None
        
        try:
            text = sarwam_stt.recognize(audio_bytes)
            return text
        except Exception as e:
            print(f"[Warning] Sarwam recognition failed: {e}")
            return None

    def _recognize_with_google(self, audio_data: sr.AudioData) -> Optional[str]:
        """Recognize speech using Google Web Speech API (fallback)"""
        try:
            text = self.recognizer.recognize_google(audio_data)
            return text
        except sr.UnknownValueError:
            return None  # silence / unintelligible
        except sr.RequestError as e:
            print(f"[Error] Google Speech API error: {e}")
            return None

    def listen_continuously(self, callback: Callable) -> None:
        if not self.microphone_available:
            print("[Error] No microphone available.")
            return

        def loop():
            while self.is_listening:
                result = self._record_clip()
                if result is None:
                    time.sleep(0.5)
                    continue
                
                audio_data, raw_bytes = result
                text = None
                
                # Try Sarwam first
                if USE_SARWAM and SARWAM_AVAILABLE:
                    text = self._recognize_with_sarwam(raw_bytes)
                
                # Fallback to Google
                if not text:
                    text = self._recognize_with_google(audio_data)
                
                if text and text.strip():
                    print(f"[Voice] Recognized: {text}")
                    callback(text)
                    
                time.sleep(0.3)  # Small delay between recordings

        self.listen_thread = threading.Thread(target=loop, daemon=True)
        self.listen_thread.start()

    def start_listening(self, callback: Callable) -> None:
        if self.is_listening:
            return
        self.is_listening = True
        self.listen_continuously(callback)
        engine = "Sarwam" if (USE_SARWAM and SARWAM_AVAILABLE) else "Google"
        print(f"[Voice] Started continuous listening ({engine} STT)...")

    def stop_listening(self) -> None:
        self.is_listening = False
        if self.listen_thread:
            self.listen_thread.join(timeout=self.record_seconds + 2)
            self.listen_thread = None
        print("[Voice] Stopped listening.")

    def listen_once(self) -> Optional[str]:
        if not self.microphone_available:
            print("[Error] No microphone available.")
            return None

        print(f"[Voice] Listening ({self.record_seconds}s)...")
        result = self._record_clip()
        if result is None:
            return None

        audio_data, raw_bytes = result
        text = None
        
        # Try Sarwam first
        if USE_SARWAM and SARWAM_AVAILABLE:
            text = self._recognize_with_sarwam(raw_bytes)
        
        # Fallback to Google
        if not text:
            text = self._recognize_with_google(audio_data)
        
        if text:
            print(f"[Voice] You said: {text}")
            return text
        
        print("[Error] Could not understand audio")
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