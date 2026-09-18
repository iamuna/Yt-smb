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
  echo FFmpeg is missing.
  where winget >nul 2>nul
  if not errorlevel 1 (
    set /p INSTALL_FFMPEG="Install FFmpeg automatically with winget? [Y/N]: "
    if /I "%INSTALL_FFMPEG%"=="Y" (
      winget install --id Gyan.FFmpeg -e --accept-package-agreements --accept-source-agreements
      echo.
      echo If FFmpeg was just installed, close this window and run setup.bat once more.
    )
  ) else (
    echo Install FFmpeg and make sure ffmpeg.exe and ffprobe.exe are on PATH.
  )
) else (
  echo FFmpeg detected.
)

echo.
echo Setup complete.
echo Double-click start.bat to launch YT SMB.
pause
exit /b 0

:error
echo.
echo Setup failed. Copy the error above if you need help.
pause
exit /b 1
