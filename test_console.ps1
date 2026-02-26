# CampusIQ Command Console Test Script
$baseUrl = "http://localhost:8000"

Write-Host ""
Write-Host "CampusIQ Command Console Test Suite" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

function Test-Login {
    param($email, $password, $role)
    Write-Host "Testing $role login..." -ForegroundColor Yellow
    
    try {
        $body = @{ email = $email; password = $password } | ConvertTo-Json
        $headers = @{ "Content-Type" = "application/json" }
        $response = Invoke-RestMethod -Uri "$baseUrl/api/auth/login" -Method Post -Body $body -Headers $headers -UseBasicParsing
        
        if ($response.access_token) {
            Write-Host "   Success: $role login OK" -ForegroundColor Green
            return $response.access_token
        }
        Write-Host "   Failed: No token received" -ForegroundColor Red
        return $null
    } catch {
        Write-Host "   Error: $_" -ForegroundColor Red
        return $null
    }
}

function Test-OperationalPlan {
    param($token, $role, $message)
    Write-Host ""
    Write-Host "Testing plan for $role - Query: $message" -ForegroundColor Yellow
    
    try {
        $body = @{ message = $message; module = "nlp"; clarification = $null } | ConvertTo-Json
        $headers = @{ "Content-Type" = "application/json"; "Authorization" = "Bearer $token" }
        $response = Invoke-RestMethod -Uri "$baseUrl/api/ops-ai/plan" -Method Post -Body $body -Headers $headers -UseBasicParsing
        
        Write-Host "   SUCCESS" -ForegroundColor Green
        Write-Host "   Plan ID: $($response.plan_id)" -ForegroundColor Cyan
        Write-Host "   Intent: $($response.intent_type)" -ForegroundColor Cyan
        Write-Host "   Entity: $($response.entity)" -ForegroundColor Cyan
        Write-Host "   Risk: $($response.risk_level)" -ForegroundColor Cyan
        Write-Host "   Status: $($response.status)" -ForegroundColor Cyan
        Write-Host "   Allowed: $($response.permission.allowed)" -ForegroundColor $(if ($response.permission.allowed) { "Green" } else { "Red" })
        if (-not $response.permission.allowed) {
            Write-Host "   Reason: $($response.permission.reason)" -ForegroundColor Red
        }
        return $true
    } catch {
        Write-Host "   FAILED: $_" -ForegroundColor Red
        return $false
    }
}

Write-Host "========================================" -ForegroundColor Magenta
Write-Host "TEST 1: ADMIN ACCESS" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
$adminToken = Test-Login -email "admin@campusiq.edu" -password "admin123" -role "ADMIN"

if ($adminToken) {
    Test-OperationalPlan -token $adminToken -role "ADMIN" -message "Show all students with CGPA below 6.0"
    Test-OperationalPlan -token $adminToken -role "ADMIN" -message "Update semester to 5 for students in section A"
    Test-OperationalPlan -token $adminToken -role "ADMIN" -message "Create new student with roll number CS3001"
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "TEST 2: FACULTY ACCESS" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
$facultyToken = Test-Login -email "faculty1@campusiq.edu" -password "faculty123" -role "FACULTY"

if ($facultyToken) {
    Test-OperationalPlan -token $facultyToken -role "FACULTY" -message "Show all students in my department"
    Test-OperationalPlan -token $facultyToken -role "FACULTY" -message "Update CGPA to 7.5 for student CS2101"
    Test-OperationalPlan -token $facultyToken -role "FACULTY" -message "Create attendance record for course CS301"
    Test-OperationalPlan -token $facultyToken -role "FACULTY" -message "Delete attendance record from yesterday"
}

Write-Host ""
Write-Host "Test Complete!" -ForegroundColor Green
Write-Host "Manual test: Open http://localhost:5174 and login" -ForegroundColor Yellow
