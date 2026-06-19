"""
Pluto AI - Main Entry Point
Run this first to initialize the system, then run app.py for web interface
"""

import os
import sys
import traceback
from pathlib import Path

# Ensure Backend is discoverable
sys.path.append(os.path.join(os.path.dirname(__file__), 'Backend'))
sys.path.append(os.path.dirname(__file__))

def check_and_install_dependencies() -> None:
    """Verify and install dependencies using pip"""
    required = {
        "flask": "Flask==3.0.0",
        "flask_cors": "Flask-CORS==4.0.0",
        "dotenv": "python-dotenv==1.0.0",
        "edge_tts": "edge-tts==6.1.10",
        "groq": "groq==0.9.0",
        "cohere": "cohere==5.0.1",
        "requests": "requests==2.31.0",
        "pyautogui": "pyautogui==0.9.53",
        "speech_recognition": "SpeechRecognition==3.10.0",
        "PyQt5": "pyQt5==5.15.9",
        "PIL": "pillow==10.1.0",
        "googlesearch": "googlesearch-python==1.2.3",
        "rich": "rich==13.7.0",
        "numpy": "numpy>=1.20.0",
        "sounddevice": "sounddevice>=0.4.0",
        "scipy": "scipy>=1.7.0",
        "pygame": "pygame>=2.0.0",
        "psutil": "psutil>=5.9.0"
    }
    
    missing = []
    for module, package in required.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
            
    if missing:
        print(f"[System] Verifying environment dependencies...")
        print(f"[System] Missing packages: {missing}")
        print("[System] Setting up environment, please wait...")
        import subprocess
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
            print("[System] ✓ Setup complete!")
        except Exception as e:
            print(f"[Error] Installation failed: {e}")
            print("[System] Attempting to install all from Requirements.txt...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "Requirements.txt"])
                print("[System] ✓ Setup complete from Requirements.txt!")
            except Exception as ex:
                print(f"[Error] Failed to install requirements: {ex}")



def setup_directories() -> None:
    """Create necessary directories"""
    directories = ["Data", "Generated_Images", "Frontend", "Backend"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    print("[System] ✓ Directory structure ready")


def start_gui() -> None:
    """Launch the GUI interface"""
    try:
        from Frontend.GUI import main as start_gui_func
        print("[System] 🎨 Launching GUI...")
        start_gui_func()
    except Exception as e:
        print(f"[Error] Failed to launch GUI: {e}")
        traceback.print_exc()
        raise ImportError("GUI launch failed") from e


def start_console() -> None:
    """Start bot in console mode"""
    print("[System] 💬 Starting console mode...")
    bot = BotCore()
    bot.start()


def main() -> None:
    """Main function to start the bot"""
    try:
        setup_directories()
        
        print("\n" + "="*60)
        print("🤖 Pluto AI System Starting...")
        print("="*60)
        
        try:
            start_gui()
        except (ImportError, Exception) as e:
            print(f"[System] GUI unavailable. Falling back to console mode...")
            try:
                start_console()
            except Exception as console_error:
                print(f"[Error] Console mode failed: {console_error}")
                traceback.print_exc()
                
    except KeyboardInterrupt:
        print("\n[System] Bot stopped by user. Goodbye! 👋")
    except Exception as e:
        print(f"[Error] Unexpected error: {e}")
        traceback.print_exc()
    finally:
        print("[System] Cleaning up...")


if __name__ == "__main__":
    check_and_install_dependencies()
    from Backend.botcore import BotCore
    main()