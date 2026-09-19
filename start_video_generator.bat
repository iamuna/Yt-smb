@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "COMFY_ROOT=%~dp0vendor\ComfyUI_windows_portable"
set "COMFY_APP=%COMFY_ROOT%\ComfyUI"
set "PYTHON=%COMFY_ROOT%\python_embeded\python.exe"
if not exist "%PYTHON%" set "PYTHON=%COMFY_ROOT%\python_embedded\python.exe"

if not exist "%COMFY_APP%\main.py" (
  echo ComfyUI is not installed yet.
  echo Running the one-time local video generator setup...
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\install_video_generator.ps1"
  if errorlevel 1 (
    echo.
    echo Video generator setup failed.
    pause
    exit /b 1
  )
)

if not exist "%PYTHON%" (
  echo ComfyUI embedded Python was not found.
  echo Run tools\install_video_generator.ps1 again.
  pause
  exit /b 1
)

echo ========================================
echo      YT SMB LOCAL VIDEO GENERATOR
echo ========================================
echo.
echo Starting ComfyUI at http://127.0.0.1:8188
echo Low-VRAM mode is enabled for wider GPU compatibility.
echo Keep this window open while generating video.
echo.

"%PYTHON%" -s "%COMFY_APP%\main.py" --windows-standalone-build --listen 127.0.0.1 --port 8188 --lowvram --disable-auto-launch

echo.
echo ComfyUI stopped.
pause
