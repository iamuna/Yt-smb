@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo        YT SMB - FIRST TIME SETUP
echo ========================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found.
  echo Install Python 3.11 or newer from python.org and enable "Add Python to PATH".
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 goto :error
)

echo Updating pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :error

echo Installing app dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo.
where ffmpeg >nul 2>nul
if errorlevel 1 (
  echo WARNING: FFmpeg is not on PATH yet.
  echo The app will open, but video creation needs FFmpeg.
) else (
  echo FFmpeg detected.
)

echo.
echo Setup complete.
echo You can now double-click start.bat
pause
exit /b 0

:error
echo.
echo Setup failed. Copy the error above if you need help.
pause
exit /b 1
