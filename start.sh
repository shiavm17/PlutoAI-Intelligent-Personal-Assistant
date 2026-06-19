#!/bin/bash

# Pluto AI - Quick Start Launcher for Unix/Linux/Mac

echo ""
echo "========================================"
echo "  Pluto AI - Quick Start"
echo "========================================"
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8+ from https://www.python.org/"
    exit 1
fi

echo "Python version: $(python3 --version)"
echo ""

while true; do
    echo "Select an option:"
    echo "1. Install dependencies (first time setup)"
    echo "2. Run Main.py (Bot system)"
    echo "3. Run app.py (Web server)"
    echo "4. Run both (in background)"
    echo "5. View setup instructions"
    echo "6. Exit"
    echo ""
    read -p "Enter your choice (1-6): " choice

    case $choice in
        1)
            echo ""
            echo "Installing dependencies..."
            pip3 install -r Requirements.txt --upgrade
            echo ""
            echo "Setup complete! Now run this script again to start the bot."
            read -p "Press Enter to continue..."
            ;;
        2)
            echo ""
            echo "Starting Main.py..."
            python3 Main.py
            ;;
        3)
            echo ""
            echo "Starting app.py..."
            echo "Please ensure Main.py is running in another terminal!"
            echo ""
            echo "Web server will start at http://localhost:5000"
            python3 app.py
            ;;
        4)
            echo ""
            echo "Starting both services in background..."
            echo ""
            nohup python3 Main.py > main.log 2>&1 &
            MAIN_PID=$!
            echo "Main.py started (PID: $MAIN_PID)"
            
            sleep 3
            
            nohup python3 app.py > app.log 2>&1 &
            APP_PID=$!
            echo "app.py started (PID: $APP_PID)"
            echo ""
            echo "Both services running in background!"
            echo "Open browser at http://localhost:5000"
            echo ""
            echo "To stop services later, run:"
            echo "  kill $MAIN_PID $APP_PID"
            echo ""
            read -p "Press Enter to continue..."
            ;;
        5)
            echo ""
            echo "Opening SETUP.md..."
            if command -v open &> /dev/null; then
                # macOS
                open SETUP.md
            elif command -v xdg-open &> /dev/null; then
                # Linux
                xdg-open SETUP.md
            else
                # Fallback to cat
                cat SETUP.md | less
            fi
            ;;
        6)
            exit 0
            ;;
        *)
            echo "Invalid choice!"
            ;;
    esac
done
