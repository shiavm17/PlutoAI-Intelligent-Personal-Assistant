# 🤖 Pluto AI - Intelligent Personal Assistant

<div align="center">

![Pluto AI](https://img.shields.io/badge/Pluto%20AI-v1.1-indigo)
![Python](https://img.shields.io/badge/Python-3.8%2B-green)
![Flask](https://img.shields.io/badge/Flask-3.0-red)
![PyQt5](https://img.shields.io/badge/GUI-PyQt5-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

**A premium, hands-free personal assistant featuring a gorgeous Light Theme and continuous Voice Wake-Word activation.**

[Features](#-features) • [Installation](#-installation) • [Quick Start](#-quick-start) • [Voice & Wake-Word Engine](#-voice--wake-word-engine) • [GitHub Push Prep](#-github-push-preparation) • [API Directory](#-api-endpoints)

</div>

---

## 🎯 Features

### 🎙️ Continuous Voice Wake-Word Engine
- **Always-Listening Standby**: Launches automatically in the background when the application starts.
- **Natural Activation**: Wake Pluto by saying **"Activate"**, **"Hey Pluto"**, **"a Pluto"**, or just **"Pluto"**.
- **Dynamic Greetings**: Responds vocally using custom Microsoft Edge Neural TTS voices, adjusting the greeting by local time: *"Good morning/afternoon/evening boss, I am Pluto your assistant, how can I help you?"*.
- **Continuous Conversation Mode**: Once activated, Pluto stays in an active vocal session, executing consecutive speech prompts without repeating the wake phrase, until you say *"stop"* or remain silent.

### 🎨 Premium Light Theme Redesign
- **Glassmorphic Web Dashboard**: Designed with a clean, human-made aesthetic using a harmonious Slate-Indigo-Rose color palette, translucent white glass panels, subtle box-shadows, and smooth micro-animations.
- **Sleek Desktop GUI**: Formatted PyQt5 window displaying an off-white background (`#f1f5f9`) and white card layouts with readable slate typography.
- **Dynamic Waves Visualizer**: Smooth HTML Canvas drawing multi-layered sound waves that dynamically morph speed and color (Indigo, Rose, Violet) based on the bot's state (*idle, listening, processing, speaking*).

### 🤖 Intelligent Decision Engine
- **Multi-LLM Integration**: Seamless routing using Groq (distilled Llama), Cohere Command, OpenAI, and DeepSeek-R1 models.
- **Automated Task Routing**: Recognizes intent to open/close local applications, query search engines (Google, YouTube), create textual contents, generate stable-diffusion images, set reminders, or adjust system volume.

---

## 📦 Installation

### Prerequisites
- Python 3.8 or higher installed on your system.
- Microphone input device.
- Modern web browser (Chrome, Edge, Firefox, or Safari).

### Detailed Setup

1. **Clone the Repository**
   ```bash
   git clone <your-repository-url>
   cd "Pluto AI"
   ```

2. **Install Required Packages**
   ```bash
   pip install -r Requirements.txt
   ```
   *Note: On Windows, missing PyQt5, sounddevice, or pygame dependencies will be verified and installed automatically by the system loaders.*

3. **Configure Environment Keys**
   Copy the configuration template to create your own local `.env` file:
   ```bash
   cp .env.example .env
   ```
   Open the newly created `.env` file and insert your API credentials:
   ```ini
   CohereAPIKey=your_cohere_api_key
   GroqAPIKey=your_groq_api_key
   Username=YourName
   Assistantname=Pluto
   AssistantVoice=en-IN-PrabhatNeural
   MicrophoneIndex=0
   ```

---

## ⚡ Quick Start

You can run Pluto AI in multiple modes depending on your workflow.

### Option 1: Quick Launcher Utility (Recommended for Windows)
Double-click `start.bat` in the project root:
- **Option 4** runs both the **Desktop GUI** and the **Web Server** concurrently.
- **Option 5** (Hidden Mode) runs both services silently in the background. You can immediately access the dashboard in your web browser.
- **Option 7** registers the assistant to run automatically on Windows Startup.

### Option 2: Run via Terminal
Launch the main controller GUI and the local Flask server in separate terminals:
```bash
# Terminal 1: Starts Desktop Interface & Wake-Word Engine
python Main.py

# Terminal 2: Starts Flask API & Web Dashboard
python app.py
```
Open **[http://localhost:5000](http://localhost:5000)** in your browser to interact with the responsive dashboard.

---

## 🎙️ Voice & Wake-Word Engine

Pluto's voice controller functions in two distinct phases:

```
[Standby Mode]
    │
    ▼ (Say: "Activate" / "Hey Pluto" / "a Pluto" / "Pluto")
[Speech Output: "Good morning boss, I am Pluto your assistant..."]
    │
    ▼
[Active Conversation Mode] ◄──────────────┐
    │                                     │
    ├─► (Say command) ──► [Process API] ──┘ (Repeats prompt loop)
    │
    └─► (Say "stop/exit" or remain silent)
    │
    ▼
[Standby Mode] (Listens for wake phrase again)
```

### Voice Automation Prompts
Once the session is active, speak commands directly:
* **Apps**: *"Open Google"* / *"Close Notepad"*
* **Media**: *"Play jazz music"* / *"YouTube search funny cats"*
* **Knowledge**: *"Google search python tutorials"* / *"What's the weather today?"*
* **Graphics**: *"Generate image of a futuristic castle"*
* **Reminders**: *"Remind me to call the team tomorrow at 3 PM"*

---

## 🔒 GitHub Push Preparation

Before pushing this project to your public GitHub profile, the repository has been secured and refined:
- **Exclusion Configured**: A robust `.gitignore` is active, excluding your private `.env` file, local Python environments (`.conda/`, `.venv/`), Pygame/EdgeTTS audio caches (`Data/*.mp3`), log databases, and intermediate `__pycache__` compilation outputs.
- **Folder Preservation**: Empty directories required for the app's files ([Data/](file:///d:/Pluto%20AI/Data/.gitkeep) and [Generated_Images/](file:///d:/Pluto%20AI/Generated_Images/.gitkeep)) are preserved using placeholder `.gitkeep` files.
- **API Security**: No keys are hardcoded in the codebase. All connection requests are verified securely through `.env` configurations.

---

## 🌐 API Endpoints

The Flask application serves the dashboard and exposes these REST API endpoints for automation:

* **`POST /chat`**: Submit a chat query string.
  ```json
  { "message": "open youtube" }
  ```
* **`GET /api/history`**: Returns recorded chat entries.
* **`GET /api/status`**: Returns CPU, memory metrics, online status, and configured API checks.
* **`POST /api/clear-history`**: Clears saved web chat interactions.

---

## 📁 Project Structure

```
Pluto AI/
├── Main.py                      # Initializes Desktop GUI & Wake Word
├── app.py                       # Runs Flask Server and captures voice callbacks
├── start.bat                    # Windows Launcher Utility
├── start.sh                     # Linux/MacOS shell launcher
├── Requirements.txt             # Project library requirements
├── .env.example                 # Configuration template (keys omitted)
├── .gitignore                   # Excludes secret credentials & env caches
│
├── Backend/
│   ├── botcore.py              # DMM router & Background voice state loops
│   ├── chatbot.py              # LLM controller (Groq/DeepSeek)
│   ├── texttospeech.py         # Pygame audio synthesis
│   ├── speechtotext.py         # Sounddevice recording & STT Google Web API
│   ├── automation.py           # Reminders & Application opener scripts
│   ├── realtimeSearchEngine.py # Bing/Google web search engine
│   └── imageGeneration.py      # HuggingFace stable diffusion engine
│
├── Frontend/
│   ├── GUI.py                  # Light-theme PyQt5 GUI
│   ├── index.html              # Light-theme dashboard with canvas visualizer
│   └── Graphics/               # UI assets & animation resources
│
└── Data/                       # Local chat logs & speech outputs (ignored)
```

---

<div align="center">

**⭐ Star this repository if you find it helpful!**

Made with ❤️ by Shivam Chaturvedi & the Pluto AI Team

</div>
