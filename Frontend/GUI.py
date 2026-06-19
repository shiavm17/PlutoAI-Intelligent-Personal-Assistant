import sys
import os
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QPushButton, QLabel, QFrame, QLineEdit)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QMovie, QFont, QColor, QPalette, QPixmap

# Ensure Backend is discoverable
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__))))

from Backend.botcore import BotCore

class BotWorker(QThread):
    """Worker thread for processing bot commands"""
    response_signal = pyqtSignal(str)
    
    def __init__(self, bot, command):
        super().__init__()
        self.bot = bot
        self.command = command

    def run(self):
        try:
            response = self.bot.process_input(self.command)
            self.response_signal.emit(f"[Bot]: {response}")
        except Exception as e:
            self.response_signal.emit(f"[Error]: {e}")

class MainWindow(QMainWindow):
    print_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Pluto AI")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("background-color: #f1f5f9; color: #1e293b;")

        # Initialize Bot
        self.bot = BotCore(gui_mode=True)
        self.bot_worker = None
        
        # Redirect stdout
        import builtins
        self.original_print = builtins.print
        builtins.print = self.new_print
        self.print_signal.connect(self.update_chat)

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        # Left Side (GIF/Visuals)
        left_panel = QFrame()
        left_panel.setFrameShape(QFrame.StyledPanel)
        left_panel.setStyleSheet("background-color: #ffffff; border-radius: 16px; border: 1px solid #cbd5e1;")
        left_layout = QVBoxLayout(left_panel)
        
        self.gif_label = QLabel("Loading Visuals...")
        self.gif_label.setAlignment(Qt.AlignCenter)
        self.gif_label.setStyleSheet("border: none;")
        
        # Try to load GIF or Image
        gif_path = os.path.join("Data", "jarvis.gif")
        png_path = os.path.join("Data", "jarvis.png")
        
        if os.path.exists(gif_path):
            self.movie = QMovie(gif_path)
            self.movie.setScaledSize(self.gif_label.size())
            self.gif_label.setMovie(self.movie)
            self.movie.start()
        elif os.path.exists(png_path):
            self.gif_label.setPixmap(QPixmap(png_path).scaled(500, 500, Qt.KeepAspectRatio))
        else:
            self.gif_label.setText("No Visuals Found\nAdd jarvis.gif to Data folder")
            self.gif_label.setStyleSheet("color: #aaaaaa; font-size: 16px;")

        left_layout.addWidget(self.gif_label)
        layout.addWidget(left_panel, 4) # 40% width

        # Right Side (Chat & Controls)
        right_panel = QFrame()
        right_panel.setStyleSheet("background-color: #ffffff; border-radius: 16px; border: 1px solid #cbd5e1;")
        right_layout = QVBoxLayout(right_panel)

        # Chat Area
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setFont(QFont("Consolas", 11))
        self.chat_area.setStyleSheet("""
            QTextEdit {
                background-color: #f8fafc;
                color: #1e293b;
                border: 1px solid #cbd5e1;
                border-radius: 12px;
                padding: 14px;
            }
        """)
        right_layout.addWidget(self.chat_area)

        # Input Area
        input_layout = QHBoxLayout()
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your command here...")
        self.input_field.setFont(QFont("Segoe UI", 12))
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                color: #1e293b;
                border: 1px solid #cbd5e1;
                border-radius: 10px;
                padding: 10px 14px;
            }
        """)
        self.input_field.returnPressed.connect(self.send_command)
        
        self.send_btn = QPushButton("SEND")
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: #ffffff;
                padding: 10px 20px;
                border-radius: 10px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { background-color: #4f46e5; }
        """)
        self.send_btn.clicked.connect(self.send_command)
        
        self.voice_btn = QPushButton("🎤 VOICE")
        self.voice_btn.setCursor(Qt.PointingHandCursor)
        self.voice_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #334155;
                padding: 10px 20px;
                border-radius: 10px;
                font-weight: bold;
                border: 1px solid #cbd5e1;
            }
            QPushButton:hover { background-color: #e2e8f0; }
            QPushButton:checked { background-color: #f43f5e; color: #ffffff; border: none; }
        """)
        self.voice_btn.setCheckable(True)
        self.voice_btn.clicked.connect(self.toggle_voice)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)
        input_layout.addWidget(self.voice_btn)
        
        right_layout.addLayout(input_layout)
        layout.addWidget(right_panel, 6) # 60% width

        # Start Bot Initialization
        QTimer.singleShot(100, self.init_bot)

    def new_print(self, *args, **kwargs):
        sep = kwargs.get('sep', ' ')
        end = kwargs.get('end', '\n')
        text = sep.join(map(str, args)) + end
        self.print_signal.emit(text)
        self.original_print(*args, **kwargs)

    def update_chat(self, text):
        self.chat_area.moveCursor(self.chat_area.textCursor().End)
        self.chat_area.insertPlainText(text)
        self.chat_area.moveCursor(self.chat_area.textCursor().End)

    def init_bot(self):
        threading.Thread(target=self.bot.start, daemon=True).start()

    def send_command(self):
        text = self.input_field.text().strip()
        if not text:
            return
        
        self.input_field.clear()
        self.chat_area.append(f"\n[You]: {text}")
        
        # Process in background
        self.bot_worker = BotWorker(self.bot, text)
        self.bot_worker.response_signal.connect(self.handle_response)
        self.bot_worker.start()

    def handle_response(self, response):
        # The print redirection handles most output, but this ensures we catch the return value
        pass 

    def toggle_voice(self):
        if self.voice_btn.isChecked():
            self.voice_btn.setStyleSheet("background-color: #f43f5e; color: white; padding: 10px 20px; border-radius: 10px; font-weight: bold; border: none;")
            self.voice_btn.setText("🛑 STOP")
            threading.Thread(target=self.bot.start_voice_mode, daemon=True).start()
        else:
            self.voice_btn.setStyleSheet("background-color: #f1f5f9; color: #334155; padding: 10px 20px; border-radius: 10px; font-weight: bold; border: 1px solid #cbd5e1;")
            self.voice_btn.setText("🎤 VOICE")
            self.bot.stop_voice_mode()

    def closeEvent(self, event):
        import builtins
        builtins.print = self.original_print
        self.bot.stop_voice_mode()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
