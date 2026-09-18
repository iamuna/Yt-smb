@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ========================================
echo      YT SMB - FREE LOCAL SETUP
echo ========================================
echo.
echo This setup uses local AI and local speech.
echo It does not require a paid AI API key.
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found.
  echo Install Python 3.11 or newer and enable "Add Python to PATH".
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

echo Installing YT SMB dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo.
echo Checking FFmpeg...
where ffmpeg >nul 2>nul
if errorlevel 1 (
  echo FFmpeg is missing.
  where winget >nul 2>nul
  if not errorlevel 1 (
    set /p INSTALL_FFMPEG="Install free FFmpeg with winget? [Y/N]: "
    if /I "%INSTALL_FFMPEG%"=="Y" (
      winget install --id Gyan.FFmpeg -e --accept-package-agreements --accept-source-agreements
      echo FFmpeg installation command finished.
    )
  ) else (
    echo Install FFmpeg manually and add ffmpeg/ffprobe to PATH.
  )
) else (
  echo FFmpeg detected.
)

echo.
echo Checking local AI (Ollama)...
set "OLLAMA_CMD="
where ollama >nul 2>nul
if not errorlevel 1 set "OLLAMA_CMD=ollama"

if not defined OLLAMA_CMD (
  if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
    set "OLLAMA_CMD=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
  )
)

if not defined OLLAMA_CMD (
  echo Ollama is missing.
  where winget >nul 2>nul
  if not errorlevel 1 (
    set /p INSTALL_OLLAMA="Install free local Ollama with winget? [Y/N]: "
    if /I "%INSTALL_OLLAMA%"=="Y" (
      winget install --id Ollama.Ollama -e --accept-package-agreements --accept-source-agreements
      if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
        set "OLLAMA_CMD=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
      )
    )
  ) else (
    echo Install Ollama manually from the official Ollama website.
  )
) else (
  echo Ollama detected.
)

echo.
if defined OLLAMA_CMD (
  echo Checking local model qwen2.5:3b...
  "%OLLAMA_CMD%" list | findstr /I "qwen2.5:3b" >nul 2>nul
  if errorlevel 1 (
    set /p PULL_MODEL="Download the free qwen2.5:3b local model now? [Y/N]: "
    if /I "%PULL_MODEL%"=="Y" (
      "%OLLAMA_CMD%" pull qwen2.5:3b
    )
  ) else (
    echo qwen2.5:3b detected.
  )
) else (
  echo Ollama was not detected in this terminal.
  echo If it was just installed, close this window and run setup.bat again.
)

echo.
echo ========================================
echo Setup finished.
echo Double-click start.bat to launch YT SMB.
echo ========================================
pause
exit /b 0

:error
echo.
echo Setup failed. Copy the error above if you need help.
pause
exit /b 1
