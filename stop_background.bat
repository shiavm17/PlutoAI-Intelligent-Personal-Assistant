@echo off
echo ========================================
echo   Pluto AI - Stop Services
echo ========================================
echo.

echo [System] Stopping background Pluto AI processes...
taskkill /f /im pythonw.exe >nul 2>&1

echo [System] ✓ Pluto AI background services have been stopped.
echo.
pause
