@echo off
echo ============================================
echo   Sonixx - Virtual Audio Router Setup
echo ============================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Install from https://python.org
    pause
    exit /b 1
)

echo [1/2] Syncing environment...
uv sync --quiet
if %errorlevel% neq 0 (
    echo ERROR: uv sync failed.
    pause
    exit /b 1
)

echo [2/2] Launching Sonixx...
echo.
uv run main.py
pause
