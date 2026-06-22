# Backend/texttospeech.py
"""
Text-to-speech via Sarwam AI (primary) or edge-tts (fallback),
played back through pygame's mixer.
Falls back gracefully to console-only output if audio playback
isn't available.
"""

import os
import random
import asyncio
from pathlib import Path

from dotenv import dotenv_values

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "Data"
SPEECH_FILE = DATA_DIR / "speech.mp3"

env_vars = dotenv_values(BASE_DIR.parent / ".env")
AssistantVoice = env_vars.get("AssistantVoice", "en-US-AriaNeural")
SarwamAPIKey = env_vars.get("SarwamAPIKey", "")
USE_SARWAM = SarwamAPIKey.strip() != ""

# Import Sarwam AI if available
try:
    from sarwamAI import text_to_speech as sarwam_tts
    SARWAM_AVAILABLE = True
except ImportError:
    SARWAM_AVAILABLE = False
    print("[Warning] Sarwam AI module not available. Using fallback (edge-tts).")

# Import edge-tts as fallback
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    print("[Warning] edge-tts not found. TTS will be limited.")

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("[Warning] Pygame not found. Audio playback will be disabled.")

_mixer_initialized = False


async def TextToAudioFile(text: str) -> None:
    """Generate audio using edge-tts (fallback method)"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if SPEECH_FILE.exists():
        try:
            os.remove(SPEECH_FILE)
        except OSError as e:
            print(f"[Warning] Could not remove old speech file: {e}")

    if not EDGE_TTS_AVAILABLE:
        print("[Error] edge-tts not available")
        return

    communicate = edge_tts.Communicate(text, AssistantVoice, pitch="+5Hz", rate="+13%")
    await communicate.save(str(SPEECH_FILE))


def _ensure_mixer() -> bool:
    global _mixer_initialized
    if not PYGAME_AVAILABLE:
        return False
    if not _mixer_initialized:
        pygame.mixer.init()
        _mixer_initialized = True
    return True


def TTS(text: str, func=lambda r=None: True) -> bool:
    """Generate speech audio and play it. Try Sarwam first, fallback to edge-tts.
    `func()` is polled during playback (returning False stops early);
    `func(False)` is called once playback ends."""
    
    # Try Sarwam AI first if available
    if USE_SARWAM and SARWAM_AVAILABLE:
        try:
            print("[Voice] Using Sarwam AI TTS")
            return sarwam_tts(text, func)
        except Exception as e:
            print(f"[Warning] Sarwam TTS failed: {e}. Falling back to edge-tts...")
    
    # Fallback to edge-tts
    if not EDGE_TTS_AVAILABLE:
        print(f"[Voice] (audio disabled) {text}")
        try:
            func(False)
        except Exception:
            pass
        return False
    
    try:
        asyncio.run(TextToAudioFile(text))
    except Exception as e:
        print(f"[Error] generating speech audio: {e}")
        return False

    if not _ensure_mixer():
        print(f"[Voice] (audio disabled) {text}")
        try:
            func(False)
        except Exception:
            pass
        return False

    try:
        pygame.mixer.music.load(str(SPEECH_FILE))
        pygame.mixer.music.play()

        clock = pygame.time.Clock()
        while pygame.mixer.music.get_busy():
            if func() is False:
                break
            clock.tick(10)

        return True

    except Exception as e:
        print(f"[Error] in TTS playback: {e}")
        return False

    finally:
        try:
            func(False)
        except Exception:
            pass
        try:
            if PYGAME_AVAILABLE:
                pygame.mixer.music.stop()
        except Exception:
            pass


_HEARD_MORE_RESPONSES = [
    "The rest of the result has been printed to the chat screen, kindly check it out sir.",
    "The rest of the text is now on the chat screen, sir, please check it.",
    "You can see the rest of the text on the chat screen, sir.",
    "The remaining part of the text is now on the chat screen, sir.",
    "Sir, you'll find more text on the chat screen for you to see.",
    "The rest of the answer is now on the chat screen, sir.",
    "Sir, please look at the chat screen, the rest of the answer is there.",
    "You'll find the complete answer on the chat screen, sir.",
    "The next part of the text is on the chat screen, sir.",
    "Sir, please check the chat screen for more information.",
    "There's more text on the chat screen for you, sir.",
    "Sir, take a look at the chat screen for additional text.",
    "You'll find more to read on the chat screen, sir.",
    "Sir, check the chat screen for the rest of the text.",
    "The chat screen has the rest of the text, sir.",
    "There's more to see on the chat screen, sir, please look.",
    "Sir, the chat screen holds the continuation of the text.",
    "You'll find the complete answer on the chat screen, kindly check it out sir.",
    "Please review the chat screen for the rest of the text, sir.",
    "Sir, look at the chat screen for the complete answer.",
]


def TextToSpeech(text: str, func=lambda r=None: True) -> bool:
    sentences = str(text).split(".")

    if len(sentences) > 4 and len(text) >= 250:
        short_text = ". ".join(s for s in sentences[:2] if s.strip())
        return TTS(f"{short_text}. {random.choice(_HEARD_MORE_RESPONSES)}", func)

    return TTS(text, func)


if __name__ == "__main__":
    while True:
        try:
            text = input("Enter the text: ")
        except (EOFError, KeyboardInterrupt):
            break
        if text.strip().lower() in {"exit", "quit"}:
            break
        TextToSpeech(text)