@echo off
chcp 65001 >nul
cd /d "%~dp0"
if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe merge_prices.py %*
) else (
    python merge_prices.py %*
)
pause
