# Backend/sarwamAI.py
"""
Sarwam AI Integration Module
Provides Text-to-Speech (TTS) and Speech-to-Text (STT) using Sarwam AI API
Supports multiple languages and high-quality audio synthesis
"""

import os
import io
import time
import threading
import requests
from pathlib import Path
from typing import Optional, Callable
from dotenv import dotenv_values

# Audio processing
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wav

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "Data"
SPEECH_FILE = DATA_DIR / "speech_sarwam.mp3"
WAV_FILE = DATA_DIR / "recording.wav"

env_vars = dotenv_values(BASE_DIR.parent / ".env")
SARWAM_API_KEY = env_vars.get("SarwamAPIKey", "")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "PlutoAI")
AssistantVoice = env_vars.get("AssistantVoice", "en-IN-neural")  # Sarwam format

# Sarwam API endpoints
SARWAM_TTS_ENDPOINT = "https://api.sarwam.com/api/v1/tts"
SARWAM_STT_ENDPOINT = "https://api.sarwam.com/api/v1/stt"

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("[Warning] Pygame not found. Audio playback will be disabled.")

_mixer_initialized = False


class SarwamTTS:
    """Sarwam AI Text-to-Speech Engine"""
    
    def __init__(self):
        self.api_key = SARWAM_API_KEY
        self.voice = AssistantVoice
        self.endpoint = SARWAM_TTS_ENDPOINT
        
        if not self.api_key:
            print("[Warning] SarwamAPIKey not set in .env — TTS will not work")
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
    
    def synthesize(self, text: str, language: str = "en") -> bool:
        """Synthesize text to speech and save as audio file"""
        if not text.strip():
            return False
        
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            
            # Remove old file if exists
            if SPEECH_FILE.exists():
                try:
                    os.remove(SPEECH_FILE)
                except OSError as e:
                    print(f"[Warning] Could not remove old speech file: {e}")
            
            # Prepare request payload
            payload = {
                "text": text,
                "voice": self.voice,
                "language": language,
                "speed": 1.0,
                "pitch": 1.0,
                "format": "mp3"
            }
            
            # Make API request
            response = self.session.post(
                self.endpoint,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"[Error] Sarwam TTS API error: {response.status_code} - {response.text}")
                return False
            
            # Save audio file
            with open(SPEECH_FILE, 'wb') as f:
                f.write(response.content)
            
            print(f"[Voice] TTS synthesis complete: {len(text)} chars")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"[Error] TTS request failed: {e}")
            return False
        except Exception as e:
            print(f"[Error] TTS synthesis failed: {e}")
            return False
    
    def play_audio(self, audio_path: str, callback: Callable = None) -> bool:
        """Play synthesized audio file"""
        if not PYGAME_AVAILABLE:
            print(f"[Voice] (audio playback disabled)")
            if callback:
                try:
                    callback(False)
                except Exception:
                    pass
            return False
        
        try:
            global _mixer_initialized
            if not _mixer_initialized:
                pygame.mixer.init()
                _mixer_initialized = True
            
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
            
            clock = pygame.time.Clock()
            while pygame.mixer.music.get_busy():
                if callback and callback() is False:
                    break
                clock.tick(10)
            
            return True
            
        except Exception as e:
            print(f"[Error] Audio playback failed: {e}")
            return False
        finally:
            if callback:
                try:
                    callback(False)
                except Exception:
                    pass
            try:
                if PYGAME_AVAILABLE:
                    pygame.mixer.music.stop()
            except Exception:
                pass


class SarwamSTT:
    """Sarwam AI Speech-to-Text Engine"""
    
    def __init__(self, samplerate: int = 16000, channels: int = 1):
        self.api_key = SARWAM_API_KEY
        self.endpoint = SARWAM_STT_ENDPOINT
        self.samplerate = samplerate
        self.channels = channels
        self.dtype = "int16"
        
        self.is_listening = False
        self.listen_thread: Optional[threading.Thread] = None
        
        if not self.api_key:
            print("[Warning] SarwamAPIKey not set in .env — STT will not work")
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}"
        })
        
        try:
            sd.query_devices()
            self.microphone_available = True
            print("[Voice] Microphone initialized (Sarwam STT)")
        except Exception as e:
            print(f"[Error] initializing microphone: {e}")
            self.microphone_available = False
    
    @property
    def microphone(self) -> bool:
        return self.microphone_available
    
    def _record_clip(self, record_seconds: int = 5) -> Optional[bytes]:
        """Record audio from microphone"""
        try:
            print(f"[Voice] Recording for {record_seconds} seconds...")
            recording = sd.rec(
                int(record_seconds * self.samplerate),
                samplerate=self.samplerate,
                channels=self.channels,
                dtype=self.dtype
            )
            sd.wait()
            
            # Convert to WAV bytes
            buf = io.BytesIO()
            wav.write(buf, self.samplerate, recording)
            buf.seek(0)
            return buf.getvalue()
            
        except Exception as e:
            print(f"[Error] recording audio: {e}")
            return None
    
    def recognize(self, audio_data: bytes, language: str = "en") -> Optional[str]:
        """Send audio to Sarwam API for transcription"""
        try:
            files = {
                'audio': ('audio.wav', io.BytesIO(audio_data), 'audio/wav')
            }
            data = {
                'language': language
            }
            
            response = self.session.post(
                self.endpoint,
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"[Error] Sarwam STT API error: {response.status_code} - {response.text}")
                return None
            
            result = response.json()
            text = result.get('text', '').strip()
            
            if text:
                print(f"[Voice] Recognized: {text}")
                return text
            
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"[Error] STT request failed: {e}")
            return None
        except Exception as e:
            print(f"[Error] STT recognition failed: {e}")
            return None
    
    def listen_continuously(self, callback: Callable, record_seconds: int = 5) -> None:
        """Continuously listen and recognize speech"""
        if not self.microphone_available:
            print("[Error] No microphone available.")
            return
        
        def loop():
            while self.is_listening:
                try:
                    audio_data = self._record_clip(record_seconds)
                    if audio_data is None:
                        time.sleep(0.5)
                        continue
                    
                    text = self.recognize(audio_data)
                    if text:
                        callback(text)
                except Exception as e:
                    print(f"[Error] in continuous listening: {e}")
                    time.sleep(1)
        
        self.listen_thread = threading.Thread(target=loop, daemon=True)
        self.listen_thread.start()
    
    def start_listening(self, callback: Callable, record_seconds: int = 5) -> None:
        """Start continuous listening"""
        if self.is_listening:
            return
        self.is_listening = True
        self.listen_continuously(callback, record_seconds)
        print("[Voice] Started continuous listening (Sarwam)...")
    
    def stop_listening(self) -> None:
        """Stop listening"""
        self.is_listening = False
        if self.listen_thread:
            self.listen_thread.join(timeout=5)
            self.listen_thread = None
        print("[Voice] Stopped listening.")
    
    def listen_once(self, record_seconds: int = 5) -> Optional[str]:
        """Listen once and return recognized text"""
        if not self.microphone_available:
            print("[Error] No microphone available.")
            return None
        
        audio_data = self._record_clip(record_seconds)
        if audio_data is None:
            return None
        
        return self.recognize(audio_data)


# Global instances
tts_engine = None
stt_engine = None


def initialize_sarwam():
    """Initialize Sarwam AI engines"""
    global tts_engine, stt_engine
    try:
        tts_engine = SarwamTTS()
        stt_engine = SarwamSTT()
        print("[System] ✓ Sarwam AI engines initialized")
        return True
    except Exception as e:
        print(f"[Error] Failed to initialize Sarwam: {e}")
        return False


def text_to_speech(text: str, callback: Callable = None) -> bool:
    """Convert text to speech using Sarwam AI"""
    if not tts_engine:
        initialize_sarwam()
    
    if not tts_engine or not tts_engine.api_key:
        print("[Error] TTS engine not available")
        return False
    
    try:
        # Synthesize audio
        if not tts_engine.synthesize(text):
            return False
        
        # Play audio
        return tts_engine.play_audio(str(SPEECH_FILE), callback)
        
    except Exception as e:
        print(f"[Error] TTS failed: {e}")
        return False


def speech_to_text(record_seconds: int = 5) -> Optional[str]:
    """Convert speech to text using Sarwam AI"""
    if not stt_engine:
        initialize_sarwam()
    
    if not stt_engine or not stt_engine.api_key:
        print("[Error] STT engine not available")
        return None
    
    try:
        return stt_engine.listen_once(record_seconds)
    except Exception as e:
        print(f"[Error] STT failed: {e}")
        return None


def start_continuous_listening(callback: Callable) -> None:
    """Start continuous speech recognition"""
    if not stt_engine:
        initialize_sarwam()
    
    if stt_engine and stt_engine.api_key:
        stt_engine.start_listening(callback)


def stop_continuous_listening() -> None:
    """Stop continuous speech recognition"""
    if stt_engine:
        stt_engine.stop_listening()


if __name__ == "__main__":
    # Test the Sarwam AI integration
    initialize_sarwam()
    
    while True:
        print("\nSarwam AI Test Menu:")
        print("1. Test TTS (Text to Speech)")
        print("2. Test STT (Speech to Text)")
        print("3. Exit")
        
        choice = input("Choose option (1-3): ").strip()
        
        if choice == "1":
            text = input("Enter text to speak: ").strip()
            if text:
                text_to_speech(text)
        elif choice == "2":
            print("Listening...")
            result = speech_to_text(5)
            if result:
                print(f"You said: {result}")
        elif choice == "3":
            break
        else:
            print("Invalid choice")
