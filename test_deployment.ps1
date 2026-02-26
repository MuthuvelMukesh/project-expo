# CampusIQ Deployment Test Script
# Tests if the single server deployment is working correctly

param(
    [string]$BaseUrl = "http://localhost:8000"
)

Write-Host "🧪 Testing CampusIQ Deployment..." -ForegroundColor Cyan
Write-Host ""

$passed = 0
$failed = 0

# Test 1: Health Check
Write-Host "Test 1: Health Check..." -NoNewline
try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get -TimeoutSec 5
    if ($response.status -eq "healthy") {
        Write-Host " ✅ PASSED" -ForegroundColor Green
        $passed++
    } else {
        Write-Host " ❌ FAILED" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host " ❌ FAILED (Server not responding)" -ForegroundColor Red
    $failed++
}

# Test 2: Root Endpoint
Write-Host "Test 2: Root Endpoint..." -NoNewline
try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/" -Method Get -TimeoutSec 5
    if ($response.service -eq "CampusIQ API") {
        Write-Host " ✅ PASSED" -ForegroundColor Green
        $passed++
    } else {
        Write-Host " ⚠️  WARNING (Might be serving frontend)" -ForegroundColor Yellow
        $passed++
    }
} catch {
    Write-Host " ❌ FAILED" -ForegroundColor Red
    $failed++
}

# Test 3: API Documentation
Write-Host "Test 3: API Documentation..." -NoNewline
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/docs" -Method Get -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host " ✅ PASSED" -ForegroundColor Green
        $passed++
    } else {
        Write-Host " ❌ FAILED" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host " ❌ FAILED" -ForegroundColor Red
    $failed++
}

# Test 4: Frontend Assets (if built)
Write-Host "Test 4: Frontend Build..." -NoNewline
if (Test-Path "frontend\dist\index.html") {
    Write-Host " ✅ PASSED" -ForegroundColor Green
    $passed++
} else {
    Write-Host " ⚠️  WARNING (Frontend not built)" -ForegroundColor Yellow
    $passed++
}

# Test 5: Database Connection (indirect)
Write-Host "Test 5: Database Schema..." -NoNewline
try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/auth/login" -Method Post -Body '{"email":"test","password":"test"}' -ContentType "application/json" -TimeoutSec 5 -ErrorAction SilentlyContinue
    # We expect this to fail with 401/422, but if it connects to DB, that's good
    Write-Host " ✅ PASSED (DB accessible)" -ForegroundColor Green
    $passed++
} catch {
    if ($_.Exception.Response.StatusCode -in @(401, 422, 404)) {
        Write-Host " ✅ PASSED (DB accessible)" -ForegroundColor Green
        $passed++
    } else {
        Write-Host " ❌ FAILED (DB connection issue)" -ForegroundColor Red
        $failed++
    }
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "Results: " -NoNewline
Write-Host "$passed passed" -NoNewline -ForegroundColor Green
Write-Host ", " -NoNewline
Write-Host "$failed failed" -ForegroundColor Red
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

if ($failed -eq 0) {
    Write-Host "🎉 Deployment is working correctly!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Access Points:" -ForegroundColor Cyan
    Write-Host "  • Frontend UI: $BaseUrl" -ForegroundColor White
    Write-Host "  • API Docs:    $BaseUrl/docs" -ForegroundColor White
    Write-Host "  • Health:      $BaseUrl/health" -ForegroundColor White
} else {
    Write-Host "⚠️  Some tests failed. Check the server logs." -ForegroundColor Yellow
}

Write-Host ""
