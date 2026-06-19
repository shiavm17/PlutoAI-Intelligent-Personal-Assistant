@echo off
REM Pluto AI - Quick Start Launcher for Windows
REM This script helps set up and run Pluto AI easily

echo.
echo ========================================
echo   Pluto AI - Quick Start
echo ========================================
echo.

REM Set python and pip executables, using local .conda if available
set PYTHON_EXE=python
set PIP_EXE=pip

if exist ".conda\python.exe" (
    echo [System] Local .conda environment detected. Using local Python.
    set PYTHON_EXE=.conda\python.exe
    set PIP_EXE=.conda\python.exe -m pip
) else (
    REM Check Python installation
    python --version >nul 2>&1
    if errorlevel 1 (
        echo Error: Python is not installed or not in PATH
        echo Please install Python 3.8+ from https://www.python.org/
        pause
        exit /b 1
    )
)

echo.
echo Select an option:
echo 1. Install dependencies (first time setup)
echo 2. Run Main.py (Bot system - Terminal Mode)
echo 3. Run app.py (Web server - Terminal Mode)
echo 4. Run both (Terminal Mode in separate windows)
echo 5. Run both in BACKGROUND (Always-On/Hidden Mode)
echo 6. Stop all background services
echo 7. Register to run automatically on Windows Startup
echo 8. Unregister from Windows Startup
echo 9. Exit
echo.

set /p choice="Enter your choice (1-9): "

if "%choice%"=="1" (
    echo.
    echo Installing dependencies...
    %PIP_EXE% install -r Requirements.txt --upgrade
    echo.
    echo Setup complete! Now run this script again to start the bot.
    pause
    exit /b 0
)

if "%choice%"=="2" (
    echo.
    echo Starting Main.py...
    %PYTHON_EXE% Main.py
    pause
    exit /b 0
)

if "%choice%"=="3" (
    echo.
    echo Starting app.py...
    echo Please ensure Main.py is running in another window!
    echo.
    echo Web server will start at http://localhost:5000
    %PYTHON_EXE% app.py
    pause
    exit /b 0
)

if "%choice%"=="4" (
    echo.
    echo Starting both services...
    echo.
    echo Starting Main.py in new window...
    start "Pluto AI - Main" %PYTHON_EXE% Main.py
    echo.
    echo Waiting 3 seconds before starting app.py...
    timeout /t 3 /nobreak
    echo.
    echo Starting app.py in new window...
    start "Pluto AI - Web Server" %PYTHON_EXE% app.py
    echo.
    echo Both services are starting!
    echo Open browser at http://localhost:5000
    pause
    exit /b 0
)

if "%choice%"=="5" (
    echo.
    echo Starting both services in the background (Hidden Mode)...
    start "" wscript.exe "%~dp0start_hidden.vbs"
    echo [System] Pluto AI has been started silently in the background.
    echo Open your browser at http://localhost:5000 to interact!
    pause
    exit /b 0
)

if "%choice%"=="6" (
    echo.
    call "%~dp0stop_background.bat"
    exit /b 0
)

if "%choice%"=="7" (
    echo.
    echo Registering Pluto AI to run at Windows Startup...
    powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%USERPROFILE%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\PlutoAI.lnk');$s.TargetPath='%~dp0start_hidden.vbs';$s.WorkingDirectory='%~dp0';$s.Save()"
    echo [System] ✓ Pluto AI registered! It will now start automatically in the background when you turn on your PC.
    pause
    exit /b 0
)

if "%choice%"=="8" (
    echo.
    echo Unregistering Pluto AI from Windows Startup...
    if exist "%USERPROFILE%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\PlutoAI.lnk" (
        del "%USERPROFILE%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\PlutoAI.lnk"
        echo [System] ✓ Pluto AI unregistered successfully from Startup.
    ) else (
        echo [System] Pluto AI was not registered in Startup.
    )
    pause
    exit /b 0
)

if "%choice%"=="9" (
    exit /b 0
)

echo Invalid choice!
pause
exit /b 1

