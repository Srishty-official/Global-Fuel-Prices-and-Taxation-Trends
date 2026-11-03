@echo off
echo ========================================================
echo Launching Global Fuel Prices Analytics Fullstack Platform
echo ========================================================
set PYTHON_EXE=C:\Users\HP\.gemini\antigravity\scratch\python311\python.exe
if exist "%PYTHON_EXE%" (
    echo Using portable Python runtime at %PYTHON_EXE%
    "%PYTHON_EXE%" app.py
) else (
    echo Using system Python runtime
    python app.py
)
pause
