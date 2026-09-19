@echo off
setlocal
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\start_video_generator.ps1"
if errorlevel 1 (
  echo.
  echo Local video generator stopped with an error.
  pause
  exit /b 1
)

pause
