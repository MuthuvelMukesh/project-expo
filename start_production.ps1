# CampusIQ Production Server Startup Script (PowerShell)
# Starts the combined server (Backend serving Frontend)

param(
    [string]$HostAddress = "0.0.0.0",
    [int]$Port = 8000
)

Write-Host "🚀 Starting CampusIQ Production Server..." -ForegroundColor Cyan
Write-Host ""

# Check if frontend build exists
if (-not (Test-Path "frontend\dist\index.html")) {
    Write-Host "⚠️  Frontend build not found. Building now..." -ForegroundColor Yellow
    .\build_production.ps1
}

# Change to backend directory
Set-Location backend

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

# Install/update dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Run database seed (optional, checks if needed)
Write-Host "🌱 Seeding database..." -ForegroundColor Yellow
python -m app.seed_db

Write-Host ""
Write-Host "✅ Server starting on http://${HostAddress}:${Port}" -ForegroundColor Green
Write-Host "📊 API Documentation: http://localhost:${Port}/docs" -ForegroundColor Cyan
Write-Host "🎨 Frontend UI: http://localhost:${Port}/" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the server
uvicorn app.main:app --host $HostAddress --port $Port
