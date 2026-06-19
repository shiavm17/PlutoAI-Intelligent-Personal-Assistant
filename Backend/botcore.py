import cohere
from rich import print
from dotenv import dotenv_values
import os
import sys
from functools import lru_cache
from typing import List, Optional

# Ensure we can import sibling modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot import ChatBot
from realtimeSearchEngine import RealtimeSearchEngine
from texttospeech import TextToSpeech
from speechtotext import SpeechToText
from automation import AutomationSystem, start_reminder_checker
from imageGeneration import GenerateImage

# Load environment variables
env_vars = dotenv_values(".env")
CohereAPIKey = env_vars.get("CohereAPIKey")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")

# Initialize Cohere client with error handling
co = None
if CohereAPIKey:
    try:
        co = cohere.Client(api_key=CohereAPIKey)
    except Exception as e:
        print(f"⚠️ Warning: Cohere Client failed to initialize. Decision making might fail. Error: {e}")

# Available functions for the decision model (tuple for faster lookups)
DECISION_FUNCS = (
    "exit", "general", "realtime", "open", "close", "play", 
    "generate image", "system", "content", "google search",
    "youtube search", "reminder", "deepseek"
)

messages = []

# Enhanced preamble for better decision making
preamble = f"""
You are a very accurate Decision-Making Model for {Assistantname}, which decides what kind of query is given to you.
You will decide whether a query is a 'general' query, a 'realtime' query, or is asking to perform any task or automation.
*** Do not answer any query, just decide what kind of query is given to you. ***

DECISION RULES:
-> Respond with 'general (query)' if a query can be answered by an LLM model and doesn't require up-to-date information
   Examples: 'general how can i study effectively?', 'general what is python?', 'general thanks i liked it'
   
-> Respond with 'deepseek (query)' if the user explicitly asks for DeepSeek, 'think', 'reasoning', or complex logic
   Examples: 'deepseek solve this math problem', 'deepseek think about this', 'deepseek code this'
   
-> Respond with 'realtime (query)' if a query requires up-to-date information or is about specific people/events
   Examples: 'realtime who is the current prime minister', 'realtime latest news about AI', 'realtime weather today'
   
-> Respond with 'open (application/website name)' for opening applications or websites
   Examples: 'open facebook', 'open notepad', 'open chrome'
   
-> Respond with 'close (application name)' for closing applications
   Examples: 'close notepad', 'close chrome'
   
-> Respond with 'play (song name)' for playing music
   Examples: 'play despacito', 'play classical music'
   
-> Respond with 'generate image (description)' for image generation requests
   Examples: 'generate image a cat sitting on a chair', 'generate image sunset over mountains'
   
-> Respond with 'system (task)' for system control tasks
   Examples: 'system mute', 'system volume up', 'system shutdown', 'system restart'
   
-> Respond with 'content (topic)' for content creation requests
   Examples: 'content write an email', 'content create a story', 'content write code'
   
-> Respond with 'google search (query)' for Google searches
   Examples: 'google search best restaurants nearby', 'google search python tutorials'
   
-> Respond with 'youtube search (query)' for YouTube searches
   Examples: 'youtube search funny cats', 'youtube search programming tutorials'
   
-> Respond with 'reminder (datetime with message)' for setting reminders
   Examples: 'reminder 9:00pm 25th june business meeting', 'reminder 2:00pm tomorrow call mom'

*** For multiple tasks, separate with commas: 'open facebook, close notepad, play music' ***
*** For goodbye/exit: respond with 'exit' ***
*** If unsure, default to 'general (query)' ***
"""

# Chat history for the decision model
ChatHistory = [
    {"role": "User", "message": "how are you?"},
    {"role": "Chatbot", "message": "general how are you?"},
    {"role": "User", "message": "open chrome and tell me about AI"},
    {"role": "Chatbot", "message": "open chrome, realtime tell me about AI"},
    {"role": "User", "message": "generate an image of a sunset and play relaxing music"},
    {"role": "Chatbot", "message": "generate image sunset, play relaxing music"},
    {"role": "User", "message": "remind me about the meeting at 3pm tomorrow"},
    {"role": "Chatbot", "message": "reminder 3:00pm tomorrow meeting"},
    {"role": "User", "message": "search youtube for cooking videos"},
    {"role": "Chatbot", "message": "youtube search cooking videos"},
    {"role": "User", "message": "deepseek solve this complex math"},
    {"role": "Chatbot", "message": "deepseek solve this complex math"}
]

class BotCore:
    def __init__(self, gui_mode=False):
        self.running = False
        self.gui_mode = gui_mode
        self.voice_mode = False
        self.stt = None
        self.automation = AutomationSystem()
        self.message_callbacks = []
        self.wake_word_active = True
        
        # Start reminder checker
        start_reminder_checker()
        
        print(f"[Bot] {Assistantname} Bot System Initialized!")
        print(f"[Bot] Hello {Username}!")
        
        # Start background wake-word detector thread
        import threading
        threading.Thread(target=self.start_wake_word_detector, daemon=True).start()

    def register_message_callback(self, callback):
        """Register a callback for voice/background messages"""
        self.message_callbacks.append(callback)

    def trigger_message_callbacks(self, user_msg, bot_msg):
        """Invoke all registered message callbacks"""
        for cb in self.message_callbacks:
            try:
                cb(user_msg, bot_msg)
            except Exception as e:
                print(f"[Error] in message callback: {e}")

    def start_wake_word_detector(self):
        """Background loop to continuously listen for 'Hey Pluto' wake word"""
        import time
        from speechtotext import SpeechToText
        
        # Sleep slightly on startup to let system settle
        time.sleep(2)
        
        stt = SpeechToText(record_seconds=3)
        if not stt.microphone:
            print("[Voice] Microphone not available for wake-word detector. Disabling background listening.")
            return

        print(f"[Voice] Wake-word detector started. Say 'Hey {Assistantname}' to talk!")
        
        while self.wake_word_active:
            # If the user has manually entered voice mode via a button,
            # suspend the wake-word loop to prevent device contention.
            if self.voice_mode:
                time.sleep(1)
                continue
                
            try:
                text = stt.listen_once()
                if text:
                    text_lower = text.lower().strip()
                    
                    # Match "Activate", "Hey pluto", "a pluto", or "pluto"
                    is_wake = False
                    if any(w in text_lower for w in ["activate", "hey pluto", "a pluto", "hello pluto", "hi pluto"]):
                        is_wake = True
                    elif "pluto" in text_lower and len(text_lower.split()) <= 3:
                        is_wake = True
                        
                    if is_wake:
                        print(f"[Voice] Wake word detected: '{text}'")
                        
                        from datetime import datetime
                        current_hour = datetime.now().hour
                        if 5 <= current_hour < 12:
                            greeting = "Good morning boss"
                        elif 12 <= current_hour < 18:
                            greeting = "Good afternoon boss"
                        else:
                            greeting = "Good evening boss"
                        response_msg = f"{greeting}, I am Pluto your assistant, how can I help you?"
                        
                        print(f"\n[You]: {text}")
                        print(f"[Bot]: {response_msg}")
                        
                        # Sync with web app history
                        self.trigger_message_callbacks(text, response_msg)
                        
                        # Speak it out
                        from texttospeech import TextToSpeech
                        TextToSpeech(response_msg)
                        
                        # Enter active voice session
                        self.run_voice_session(stt)
            except Exception as e:
                print(f"[Error] in wake-word detector loop: {e}")
                time.sleep(2)
                
            time.sleep(0.2)

    def run_voice_session(self, stt):
        """Active continuous conversation loop after wake-word detection"""
        import time
        from texttospeech import TextToSpeech
        
        self.voice_mode = True
        consecutive_silence = 0
        print("[Voice] Active conversation mode. Listening for your command...")
        
        while self.wake_word_active and self.voice_mode:
            try:
                command = stt.listen_once()
                if not command or not command.strip():
                    consecutive_silence += 1
                    if consecutive_silence >= 2:
                        print("[Voice] No speech detected. Returning to standby.")
                        break
                    continue
                
                consecutive_silence = 0
                command_lower = command.lower().strip()
                
                # Check for exit words
                if any(stop_cmd in command_lower for stop_cmd in ["stop", "exit", "quit", "stop listening", "goodbye"]):
                    goodbye_msg = "Goodbye boss! Standing by."
                    print(f"\n[You]: {command}")
                    print(f"[Bot]: {goodbye_msg}")
                    self.trigger_message_callbacks(command, goodbye_msg)
                    TextToSpeech(goodbye_msg)
                    break
                
                # Process the command
                print(f"\n[You]: {command}")
                response = self.process_input(command)
                print(f"[Bot]: {response}")
                
                # Sync with web app history
                self.trigger_message_callbacks(command, response)
                
                # Play response audio
                TextToSpeech(response)
                
                # Brief sleep to allow audio to finish and avoid echo
                time.sleep(0.5)
            except Exception as e:
                print(f"[Error] in active voice session: {e}")
                break
                
        self.voice_mode = False
        print(f"[Voice] Returned to standby. Say 'Hey {Assistantname}' to talk.")


    def fallback_rule_based_router(self, prompt: str) -> List[str]:
        """A robust rule-based parser that handles commands when LLM routing is unavailable"""
        p_low = prompt.lower().strip()
        
        # 1. Exit command
        if p_low in ["exit", "quit", "goodbye", "bye", "stop"]:
            return ["exit"]
            
        # 2. Image generation
        if any(w in p_low for w in ["generate image", "create image", "generate an image", "draw a", "draw an"]):
            desc = prompt
            for w in ["generate an image of", "generate image of", "generate image", "create image of", "create image", "draw an image of", "draw a"]:
                if w in p_low:
                    idx = p_low.find(w)
                    desc = prompt[idx + len(w):].strip()
                    break
            return [f"generate image {desc}"]
            
        # 3. YouTube Search / Music
        if p_low.startswith("play "):
            song = prompt[5:].strip()
            return [f"play {song}"]
            
        if any(w in p_low for w in ["youtube search", "search youtube for"]):
            query = prompt
            for w in ["youtube search", "search youtube for"]:
                if w in p_low:
                    idx = p_low.find(w)
                    query = prompt[idx + len(w):].strip()
                    break
            return [f"youtube search {query}"]
            
        # 4. Google Search
        if any(w in p_low for w in ["google search", "search google for", "search for"]):
            query = prompt
            for w in ["google search", "search google for", "search for"]:
                if w in p_low:
                    idx = p_low.find(w)
                    query = prompt[idx + len(w):].strip()
                    break
            return [f"google search {query}"]
            
        # 5. Open App / Web
        if p_low.startswith("open "):
            app = prompt[5:].strip()
            return [f"open {app}"]
            
        # 6. Close App
        if p_low.startswith("close "):
            app = prompt[6:].strip()
            return [f"close {app}"]
            
        # 7. System control
        if any(w in p_low for w in ["mute", "volume up", "volume down", "shutdown", "restart"]):
            for action in ["mute", "volume up", "volume down", "shutdown", "restart"]:
                if action in p_low:
                    return [f"system {action}"]
                    
        # 8. Reminders
        if any(w in p_low for w in ["remind me", "set a reminder", "reminder"]):
            rem_text = prompt
            for w in ["remind me to", "remind me", "set a reminder for", "reminder"]:
                if w in p_low:
                    idx = p_low.find(w)
                    rem_text = prompt[idx + len(w):].strip()
                    break
            return [f"reminder {rem_text}"]

        # 9. DeepSeek
        if any(w in p_low for w in ["deepseek", "think about", "reason about"]):
            query = prompt
            for w in ["deepseek", "think about", "reason about"]:
                if w in p_low:
                    idx = p_low.find(w)
                    query = prompt[idx + len(w):].strip()
                    break
            return [f"deepseek {query}"]
            
        # 10. Realtime Search / News
        if any(w in p_low for w in ["news", "weather", "latest", "current"]):
            return [f"realtime {prompt}"]
            
        # Default to general chat
        return [f"general {prompt}"]

    def FirstLayerDMM(self, prompt: str = "test", retry_count: int = 0) -> List[str]:
        """Enhanced Decision Making Model with optimized response validation"""
        if not co:
            return self.fallback_rule_based_router(prompt)
        
        if retry_count > 2:  # Prevent infinite recursion
            return self.fallback_rule_based_router(prompt)

        try:
            messages.append({"role": "user", "content": f"{prompt}"})

            stream = co.chat_stream(
                model='command-r',
                message=prompt,
                temperature=0.3,
                chat_history=ChatHistory,
                prompt_truncation='OFF',
                connectors=[],
                preamble=preamble
            )    

            response = "".join(
                event.text for event in stream 
                if event.event_type == "text-generation"
            ).replace("\n", "").strip()
            
            if not response:
                return self.fallback_rule_based_router(prompt)

            # Parse and validate responses
            tasks = [task.strip() for task in response.split(",") if task.strip()]
            validated_tasks = []
            
            for task in tasks:
                # Check if task matches any known function
                if any(task.startswith(func) for func in DECISION_FUNCS):
                    validated_tasks.append(task)
                elif task:
                    # Default to general for unknown tasks
                    validated_tasks.append(f"general {task}")
            
            return validated_tasks if validated_tasks else self.fallback_rule_based_router(prompt)

        except Exception as e:
            print(f"[Error] in decision making: {e}")
            return self.fallback_rule_based_router(prompt)

    def execute_decisions(self, decisions: List[str], original_prompt: str) -> List[str]:
        """Execute the decisions made by the model with optimized handler mapping"""
        results = []
        
        # Decision handler mapping for faster execution
        decision_handlers = {
            "exit": lambda d: self._handle_exit(),
            "general": lambda d: ChatBot(d.replace("general ", "", 1)),
            "deepseek": lambda d: f"[DeepSeek]: {ChatBot(d.replace('deepseek ', '', 1), model_name='deepseek-r1-distill-llama-70b')}",
            "realtime": lambda d: RealtimeSearchEngine(d.replace("realtime ", "", 1)),
            "open": lambda d: self.automation.execute_command(f"open {d.replace('open ', '', 1)}"),
            "close": lambda d: self.automation.execute_command(f"close {d.replace('close ', '', 1)}"),
            "play": lambda d: self.automation.execute_command(f"play {d.replace('play ', '', 1)}"),
            "generate image": lambda d: GenerateImage(d.replace("generate image ", "", 1)),
            "system": lambda d: self.automation.execute_command(f"system {d.replace('system ', '', 1)}"),
            "content": lambda d: ChatBot(f"Write content about: {d.replace('content ', '', 1)}"),
            "google search": lambda d: self.automation.execute_command(f"google {d.replace('google search ', '', 1)}"),
            "youtube search": lambda d: self.automation.execute_command(f"youtube {d.replace('youtube search ', '', 1)}"),
            "reminder": lambda d: self.automation.execute_command(f"reminder {d.replace('reminder ', '', 1)}"),
        }
        
        for decision in decisions:
            try:
                decision = decision.strip()
                
                # Find matching handler
                handler = None
                for key, func in decision_handlers.items():
                    if decision.startswith(key):
                        handler = func
                        break
                
                if handler:
                    if key == "exit":
                        results.append("[Bot] Goodbye! Have a great day!")
                        self.running = False
                    else:
                        result = handler(decision)
                        results.append(result)
                else:
                    # Fallback to general query
                    results.append(ChatBot(original_prompt))
                    
            except Exception as e:
                error_msg = f"[Error] executing '{decision}': {str(e)}"
                print(error_msg)
                results.append(error_msg)
        
        return results
    
    def _handle_exit(self) -> str:
        """Handle exit command"""
        self.running = False
        return "[Bot] Goodbye! Have a great day!"

    def process_input(self, user_input):
        """Process user input and return response"""
        if not user_input.strip():
            return "Please say something!"
        
        print(f"[Processing]: {user_input}")
        
        # Get decisions from the model
        decisions = self.FirstLayerDMM(user_input)
        print(f"[Decisions]: {decisions}")
        
        # Execute decisions
        results = self.execute_decisions(decisions, user_input)
        
        # Combine results
        final_response = "\n".join(results)
        return final_response

    def start_voice_mode(self):
        """Start voice interaction mode"""
        try:
            self.stt = SpeechToText()
            self.voice_mode = True
            
            def voice_callback(text):
                if self.voice_mode and text:
                    print(f"[Voice] Input: {text}")
                    
                    # Check for wake words or exit commands
                    if any(wake in text.lower() for wake in ["hey assistant", f"hey {Assistantname.lower()}", "stop listening"]):
                        if "stop" in text.lower():
                            self.stop_voice_mode()
                            return
                        else:
                            # Remove wake word
                            for wake in ["hey assistant", f"hey {Assistantname.lower()}"]:
                                text = text.lower().replace(wake, "").strip()
                    
                    if text.strip():
                        response = self.process_input(text)
                        print(f"[Bot] {Assistantname}: {response}")
                        
                        # Text to speech response
                        TextToSpeech(response)
            
            if not self.stt.microphone:
                print("[Error] No microphone available. Voice mode disabled.")
                self.voice_mode = False
                return

            self.stt.start_listening(voice_callback)
            print(f"[Voice] Mode started! Say 'Hey {Assistantname}' followed by your command.")
            print("[Info] Say 'stop listening' to exit voice mode.")
            
        except Exception as e:
            print(f"[Error] starting voice mode: {e}")
            self.voice_mode = False

    def stop_voice_mode(self):
        """Stop voice interaction mode"""
        if self.stt:
            self.stt.stop_listening()
        self.voice_mode = False
        print("[Voice] Mode stopped.")

    def run_text_mode(self):
        """Run in text input mode"""
        print("\n💬 Text Mode Active - Type your commands:")
        print("📝 Commands: 'voice' (voice mode), 'help' (show help), 'exit' (quit)")
        
        while self.running:
            try:
                user_input = input(f"\n{Username} >>> ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() == 'exit':
                    break
                elif user_input.lower() == 'voice':
                    self.start_voice_mode()
                    input("Press Enter to stop voice mode...")
                    self.stop_voice_mode()
                    continue
                elif user_input.lower() == 'help':
                    self.show_help()
                    continue
                
                response = self.process_input(user_input)
                print(f"\n[Bot] {Assistantname}: {response}")
                
                # Optional TTS for text mode
                # tts_choice = input("\n🔊 Play audio response? (y/n): ").lower()
                # if tts_choice == 'y':
                #     TextToSpeech(response)
                    
            except KeyboardInterrupt:
                print("\n[Bot] Goodbye!")
                break
            except Exception as e:
                print(f"[Error]: {e}")

    def show_help(self):
        """Show help information"""
        help_text = f"""
[Help] {Assistantname} Bot Help

AVAILABLE COMMANDS:
• General chat: "How are you?", "Tell me a joke"
• Real-time info: "What's the news?", "Current weather"
• Open apps: "Open Chrome", "Open Notepad"
• Close apps: "Close Chrome", "Close all browsers"
• Play music: "Play Despacito", "Play jazz music"
• Generate images: "Generate image of a sunset"
• System control: "Mute volume", "Restart computer"
• Set reminders: "Remind me about meeting at 3pm tomorrow"
• Search: "Google search Python tutorials", "YouTube search funny videos"
• Content creation: "Write an email", "Create a story"

VOICE COMMANDS:
• Say "Hey {Assistantname}" + your command
• Say "Stop listening" to exit voice mode

TEXT COMMANDS:
• Type 'voice' - Switch to voice mode
• Type 'help' - Show this help
• Type 'exit' - Quit the bot

EXAMPLES:
• "Open YouTube and play relaxing music"
• "Generate image of a cat, then remind me to feed pets at 6pm"
• "What's the weather today and close all browser windows"
        """
        print(help_text)

    def start(self):
        """Start the bot system"""
        self.running = True
        
        # Show welcome message
        print(f"\n[System] Welcome to {Assistantname} Bot System!")
        print(f"[System] Ready to assist you, {Username}!")
        
        if self.gui_mode:
            print("[System] GUI Mode Initialized. Waiting for commands...")
            return

        # Choose mode
        while True:
            mode = input("\n[Input] Choose mode - 'text' for keyboard input, 'voice' for speech, 'help' for info: ").lower()
            
            if mode == 'text':
                self.run_text_mode()
                break
            elif mode == 'voice':
                self.start_voice_mode()
                input("Press Enter to stop voice mode and exit...")
                self.stop_voice_mode()
                break
            elif mode == 'help':
                self.show_help()
            else:
                print("❌ Invalid choice. Please type 'text', 'voice', or 'help'")

        print(f"[System] Thank you for using {Assistantname}! Goodbye {Username}!")
