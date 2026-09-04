# Thanatos Windows One-Click Bootstrap Script
# PowerShell 5.1+ / PowerShell 7+ compatible

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   THANATOS AI ASSISTANT // AUTOMATED BOOTSTRAP WIZARD   " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "[!] Python was not found in your PATH. Please install Python 3.11 or 3.12." -ForegroundColor Red
    exit 1
}
Write-Host "[+] Python detected: $($pythonCmd.Source)" -ForegroundColor Green

# 2. Setup Virtual Environment
if (-not (Test-Path ".\venv")) {
    Write-Host "[*] Creating virtual environment (.venv)..." -ForegroundColor Yellow
    python -m venv venv
}
Write-Host "[+] Activating virtual environment..." -ForegroundColor Green
& ".\venv\Scripts\Activate.ps1"

# 3. Upgrade pip and install dependencies
Write-Host "[*] Installing Python requirements..." -ForegroundColor Yellow
& ".\venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\venv\Scripts\python.exe" -m pip install -r requirements.txt

# 4. Check / Install Playwright Browsers
Write-Host "[*] Checking Playwright browser binaries..." -ForegroundColor Yellow
& ".\venv\Scripts\python.exe" -m playwright install chromium

# 5. Check Ollama Daemon & Model
Write-Host "[*] Checking Ollama status..." -ForegroundColor Yellow
try {
    $resp = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 3 -ErrorAction Stop
    Write-Host "[+] Ollama is online and healthy!" -ForegroundColor Green
    $models = $resp.models | ForEach-Object { $_.name }
    if ($models -contains "qwen2.5:7b") {
        Write-Host "[+] Default model 'qwen2.5:7b' is installed." -ForegroundColor Green
    } else {
        Write-Host "[*] Pulling default model 'qwen2.5:7b' (this may take a few minutes)..." -ForegroundColor Yellow
        ollama pull qwen2.5:7b
    }
} catch {
    Write-Host "[!] Warning: Ollama daemon not responding on http://localhost:11434." -ForegroundColor Yellow
    Write-Host "    Make sure to run 'ollama serve' before launching Thanatos." -ForegroundColor Yellow
}

# 6. Initialize Storage & .env
if (-not (Test-Path ".\.env")) {
    Write-Host "[*] Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item ".\.env.example" ".\.env"
}

if (-not (Test-Path ".\memory_store")) {
    New-Item -ItemType Directory -Path ".\memory_store" | Out-Null
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "[+] Thanatos environment bootstrap complete!" -ForegroundColor Green
Write-Host "To start the backend:" -ForegroundColor White
Write-Host "    .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
Write-Host "    uvicorn apps.api_server.main:app --reload --port 8000" -ForegroundColor Yellow
Write-Host ""
Write-Host "To launch the Flutter client:" -ForegroundColor White
Write-Host "    cd apps\client_flutter" -ForegroundColor Yellow
Write-Host "    flutter run -d windows" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan
