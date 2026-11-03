# PowerShell runner for Global Fuel Prices Project
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Launching Global Fuel Prices Analytics Fullstack Platform" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan

$portablePy = "C:\Users\HP\.gemini\antigravity\scratch\python311\python.exe"
if (Test-Path $portablePy) {
    Write-Host "Using Python 3.11 runtime at $portablePy" -ForegroundColor Yellow
    & $portablePy app.py
} else {
    Write-Host "Using default system Python" -ForegroundColor Yellow
    python app.py
}
