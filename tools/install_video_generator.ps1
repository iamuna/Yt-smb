param(
    [switch]$SkipModels
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$VendorDir = Join-Path $RepoRoot "vendor"
$PortableDir = Join-Path $VendorDir "ComfyUI_windows_portable"
$WorkflowFile = Join-Path $RepoRoot "workflows\wan22_5b_t2v_api.json"

function Header($text) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host $text -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
}

function Require-Curl {
    $curl = Get-Command curl.exe -ErrorAction SilentlyContinue
    if (-not $curl) { throw "curl.exe is required. It is included with current Windows 10/11." }
    return $curl.Source
}

function Find-7Zip {
    $cmd = Get-Command 7z.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $common = Join-Path $env:ProgramFiles "7-Zip\7z.exe"
    if (Test-Path $common) { return $common }

    $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if ($winget) {
        Write-Host "Installing 7-Zip..."
        & $winget.Source install --id 7zip.7zip -e --accept-package-agreements --accept-source-agreements
        if (Test-Path $common) { return $common }
    }

    throw "7-Zip was not found. Install 7-Zip and run this script again."
}

function Get-FreeGB($path) {
    $root = [System.IO.Path]::GetPathRoot($path)
    $driveId = $root.TrimEnd("\")
    $drive = Get-CimInstance Win32_LogicalDisk | Where-Object { $_.DeviceID -eq $driveId }
    if ($drive) { return [math]::Round($drive.FreeSpace / 1GB, 1) }
    return $null
}

function Download-Resumable($url, $destination) {
    if (Test-Path $destination) {
        $size = (Get-Item $destination).Length
        if ($size -gt 10MB) {
            Write-Host "Already present: $(Split-Path $destination -Leaf)"
            return
        }
    }

    New-Item -ItemType Directory -Force -Path (Split-Path $destination -Parent) | Out-Null
    $curl = Require-Curl
    Write-Host "Downloading $(Split-Path $destination -Leaf)..."
    & $curl -L --fail --retry 5 --retry-delay 3 -C - -o $destination $url
    if ($LASTEXITCODE -ne 0) { throw "Download failed: $url" }
}

function Find-ComfyApp {
    $expected = Join-Path $PortableDir "ComfyUI\main.py"
    if (Test-Path $expected) { return (Split-Path -Parent $expected) }

    $main = Get-ChildItem -Path $VendorDir -Filter main.py -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match "\\ComfyUI\\main\.py$" } | Select-Object -First 1
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

Header "YT SMB - LOCAL AI VIDEO GENERATOR SETUP"
Write-Host "This installs a LOCAL video generator. No paid video-generation API is used."
Write-Host "Default model: Wan2.2 TI2V 5B"
Write-Host "Keep at least ~25 GB free for model files, cache, and output."

New-Item -ItemType Directory -Force -Path $VendorDir | Out-Null
$free = Get-FreeGB $VendorDir
if ($free -ne $null) {
    Write-Host "Free disk space: $free GB"
    if ($free -lt 25) { Write-Warning "Less than 25 GB free. Setup may run out of space." }
}

$comfyApp = Find-ComfyApp
if (-not $comfyApp) {
    Header "Downloading official ComfyUI Windows portable"

    $headers = @{ "User-Agent" = "YT-SMB-Installer" }
    $release = $null

    foreach ($repoName in @("Comfy-Org/ComfyUI", "comfyanonymous/ComfyUI")) {
        try {
            $release = Invoke-RestMethod -Headers $headers -Uri "https://api.github.com/repos/$repoName/releases/latest"
            if ($release) { break }
        } catch {
            Write-Host "Could not query $repoName; trying fallback..."
        }
    }

    if (-not $release) { throw "Could not query the official ComfyUI release." }

    $asset = $release.assets | Where-Object { $_.name -match "(?i)nvidia" -and $_.name -match "(?i)portable" -and $_.name -match "\.7z$" } | Select-Object -First 1
    if (-not $asset) {
        $asset = $release.assets | Where-Object { $_.name -match "(?i)nvidia.*\.7z$" } | Select-Object -First 1
    }
    if (-not $asset) { throw "No NVIDIA Windows portable ComfyUI archive was found in the latest official release." }

    $archive = Join-Path $VendorDir $asset.name
    Download-Resumable $asset.browser_download_url $archive

    $sevenZip = Find-7Zip
    Write-Host "Extracting ComfyUI..."
    & $sevenZip x -y $archive "-o$VendorDir"
    if ($LASTEXITCODE -ne 0) { throw "7-Zip extraction failed." }

    $comfyApp = Find-ComfyApp
    if (-not $comfyApp) { throw "ComfyUI extracted, but ComfyUI\main.py could not be found." }
} else {
    Write-Host "ComfyUI already installed: $comfyApp"
}

$pythonExe = Find-EmbeddedPython $comfyApp
if (-not $pythonExe) { throw "ComfyUI embedded Python was not found." }

Write-Host "ComfyUI app: $comfyApp"
Write-Host "Embedded Python: $pythonExe"

if (-not $SkipModels) {
    Header "Downloading Wan2.2 5B model files"

    $models = Join-Path $comfyApp "models"
    $base = "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main"

    Download-Resumable "$base/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors?download=true" (Join-Path $models "diffusion_models\wan2.2_ti2v_5B_fp16.safetensors")
    Download-Resumable "$base/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors?download=true" (Join-Path $models "text_encoders\umt5_xxl_fp8_e4m3fn_scaled.safetensors")
    Download-Resumable "$base/vae/wan2.2_vae.safetensors?download=true" (Join-Path $models "vae\wan2.2_vae.safetensors")
}

if (-not (Test-Path $WorkflowFile)) { throw "Bundled workflow is missing: $WorkflowFile" }

Header "Configuring YT SMB"

$python = Get-Command python.exe -ErrorAction SilentlyContinue
if (-not $python) { throw "System Python is required to update YT SMB settings. Run setup.bat first." }

Push-Location $RepoRoot
try {
    $configCode = "from shorts_factory.config import load_settings, save_settings; s=load_settings(); s['video_generator_provider']='comfyui_local_video'; s['comfyui_base_url']='http://127.0.0.1:8188'; s['video_workflow_file']=r'''$WorkflowFile'''; s['video_width']=480; s['video_height']=832; s['video_seconds']=5; s['video_fps']=16; s['allow_paid_services']=False; save_settings(s); print('YT SMB video generator configured.')"
    & $python.Source -c $configCode
    if ($LASTEXITCODE -ne 0) { throw "Could not update YT SMB settings." }
} finally {
    Pop-Location
}

Header "SETUP COMPLETE"
Write-Host "1. Double-click start_video_generator.bat"
Write-Host "2. Wait until ComfyUI reports http://127.0.0.1:8188"
Write-Host "3. Start YT SMB with start.bat"
Write-Host "4. Type a prompt and click GENERATE VIDEO"
Write-Host ""
Write-Host "The first generation can be slow, especially in low-VRAM mode."
