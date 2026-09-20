@echo off
setlocal
set /p GAME=Path to your Cyberpunk 2077 folder: 
python "%~dp0make_previews.py" --game "%GAME%"
pause
