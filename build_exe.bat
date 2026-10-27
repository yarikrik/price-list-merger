@echo off
chcp 65001 >nul
REM Збирає один файл "Зведення прайсів.exe" — Python на комп'ютері замовника не потрібен
cd /d "%~dp0"
python -m pip install pyinstaller openpyxl
python -m PyInstaller --onefile --name "Зведення прайсів" merge_prices.py
copy config.example.json dist\config.json
mkdir dist\input 2>nul
echo.
echo Готово: папка dist\ — exe, config.json і папка input\
pause
