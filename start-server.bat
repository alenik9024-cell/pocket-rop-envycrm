@echo off
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
echo Starting platform server. Keep this window open.
python -u "%~dp0server.py"
if errorlevel 1 (
    echo Server stopped with an error. See the message above.
    pause
)
endlocal