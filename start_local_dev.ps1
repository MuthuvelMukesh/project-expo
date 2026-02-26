# ============================================================
# CampusIQ Local Development Startup Script
# ============================================================
# This script:
# 1. Starts PostgreSQL and Redis in Docker
# 2. Waits for services to be healthy
# 3. Runs database migrations and seeding
# 4. Starts the FastAPI backend locally
#
# Prerequisites:
# - Docker Desktop running
# - Python 3.11+ installed
# - Backend dependencies installed (pip install -r backend/requirements.txt)
# ============================================================

Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         CampusIQ - Local Development Startup              ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Step 1: Start Docker Services
Write-Host "→ Step 1: Starting PostgreSQL and Redis in Docker..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to start Docker services" -ForegroundColor Red
    Write-Host "  Make sure Docker Desktop is running" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Docker services started" -ForegroundColor Green
Write-Host ""

# Step 2: Wait for services to be healthy
Write-Host "→ Step 2: Waiting for services to be healthy..." -ForegroundColor Yellow
$maxWait = 30
$waited = 0

while ($waited -lt $maxWait) {
    $dbHealth = docker inspect --format='{{.State.Health.Status}}' campusiq-db 2>$null
    $redisHealth = docker inspect --format='{{.State.Health.Status}}' campusiq-redis 2>$null
    
    if ($dbHealth -eq "healthy" -and $redisHealth -eq "healthy") {
        Write-Host "✓ All services are healthy" -ForegroundColor Green
        break
    }
    
    Write-Host "  Waiting... ($waited/$maxWait seconds)" -ForegroundColor Gray
    Start-Sleep -Seconds 2
    $waited += 2
}

if ($waited -ge $maxWait) {
    Write-Host "✗ Services did not become healthy in time" -ForegroundColor Red
    Write-Host "  Check logs: docker-compose logs" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 3: Run database migrations
Write-Host "→ Step 3: Running database migrations..." -ForegroundColor Yellow
Push-Location backend
python -m alembic upgrade head

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠ Migrations failed (may already be applied)" -ForegroundColor Yellow
}
else {
    Write-Host "✓ Migrations completed" -ForegroundColor Green
}
Pop-Location
Write-Host ""

# Step 4: Seed database
Write-Host "→ Step 4: Seeding database with initial data..." -ForegroundColor Yellow
Push-Location backend
python -m app.seed_db

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠ Database seeding failed (may already be seeded)" -ForegroundColor Yellow
}
else {
    Write-Host "✓ Database seeded" -ForegroundColor Green
}
Pop-Location
Write-Host ""

# Step 5: Start backend server
Write-Host "→ Step 5: Starting FastAPI backend server..." -ForegroundColor Yellow
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  Backend starting at: http://localhost:8000               ║" -ForegroundColor Green
Write-Host "║  API Docs at:        http://localhost:8000/docs           ║" -ForegroundColor Green
Write-Host "║                                                            ║" -ForegroundColor Green
Write-Host "║  To start frontend:                                        ║" -ForegroundColor Green
Write-Host "║    cd frontend                                             ║" -ForegroundColor Green
Write-Host "║    npm install                                             ║" -ForegroundColor Green
Write-Host "║    npm run dev                                             ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the backend server" -ForegroundColor Cyan
Write-Host ""

Push-Location backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
Pop-Location
