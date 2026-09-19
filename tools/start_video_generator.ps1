param()

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$VendorDir = Join-Path $RepoRoot "vendor"
$Installer = Join-Path $PSScriptRoot "install_video_generator.ps1"

function Find-ComfyApp {
    if (-not (Test-Path $VendorDir)) { return $null }

    $main = Get-ChildItem -Path $VendorDir -Filter main.py -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -match "\\ComfyUI\\main\.py$" } |
        Select-Object -First 1

    if ($main) { return $main.Directory.FullName }
    return $null
}

function Find-EmbeddedPython($comfyApp) {
    $parent = Split-Path -Parent $comfyApp
    $p1 = Join-Path $parent "python_embeded\python.exe"
    $p2 = Join-Path $parent "python_embedded\python.exe"

    if (Test-Path $p1) { return $p1 }
    if (Test-Path $p2) { return $p2 }
    return $null
}

$comfyApp = Find-ComfyApp

if (-not $comfyApp) {
    Write-Host "ComfyUI is not installed. Starting one-time setup..." -ForegroundColor Yellow
    & $Installer
    if ($LASTEXITCODE -ne 0) {
        throw "Video generator setup failed."
    }
    $comfyApp = Find-ComfyApp
}

if (-not $comfyApp) {
    throw "ComfyUI could not be located after setup."
}

$python = Find-EmbeddedPython $comfyApp
if (-not $python) {
    throw "ComfyUI embedded Python could not be located."
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "      YT SMB LOCAL VIDEO GENERATOR" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ComfyUI: $comfyApp"
Write-Host "URL: http://127.0.0.1:8188"
Write-Host "Mode: low VRAM"
Write-Host ""
Write-Host "Keep this window open while generating video." -ForegroundColor Yellow
Write-Host ""

& $python -s (Join-Path $comfyApp "main.py") --windows-standalone-build --listen 127.0.0.1 --port 8188 --lowvram --disable-auto-launch
