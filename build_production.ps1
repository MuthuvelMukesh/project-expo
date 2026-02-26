# CampusIQ Production Build Script
# This script builds the frontend and prepares for single-server deployment

Write-Host "🚀 Building CampusIQ for Production..." -ForegroundColor Cyan
Write-Host ""

# Step 1: Build Frontend
Write-Host "📦 Building Frontend..." -ForegroundColor Yellow
Set-Location frontend
if (Test-Path "dist") {
    Remove-Item -Recurse -Force dist
    Write-Host "✓ Cleaned previous build" -ForegroundColor Green
}
npm install
npm run build
Write-Host "✓ Frontend built successfully" -ForegroundColor Green
Write-Host ""

# Step 2: Verify build output
Set-Location ..
if (Test-Path "frontend\dist\index.html") {
    Write-Host "✓ Build verification passed" -ForegroundColor Green
} else {
    Write-Host "✗ Build verification failed - index.html not found" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 3: Display next steps
Write-Host "✅ Production build complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. cd backend" -ForegroundColor White
Write-Host "2. pip install -r requirements.txt" -ForegroundColor White
Write-Host "3. python -m app.seed_db (if needed)" -ForegroundColor White
Write-Host "4. uvicorn app.main:app --host 0.0.0.0 --port 8000" -ForegroundColor White
Write-Host ""
Write-Host "Or use Docker:" -ForegroundColor Cyan
Write-Host "docker-compose -f docker-compose.production.yml up --build" -ForegroundColor White
Write-Host ""
