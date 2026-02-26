# CampusIQ Command Console Test Script
# Tests operational AI functionality for Admin and Faculty roles

$baseUrl = "http://localhost:8000"
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     CampusIQ Command Console Test Suite                   ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

# Test credentials
$adminCreds = @{
    email = "admin@campusiq.edu"
    password = "admin123"
}

$facultyCreds = @{
    email = "faculty1@campusiq.edu"
    password = "faculty123"
}

function Test-Login {
    param($email, $password, $role)
    
    Write-Host ""
    Write-Host "🔐 Testing $role login..." -ForegroundColor Yellow
    
    try {
        $body = @{
            username = $email
            password = $password
        } | ConvertTo-Json
        
        $headers = @{
            "Content-Type" = "application/json"
        }
        
        $response = Invoke-RestMethod -Uri "$baseUrl/auth/login" -Method Post -Body $body -Headers $headers -UseBasicParsing
        
        if ($response.access_token) {
            Write-Host "   ✅ $role login successful" -ForegroundColor Green
            return $response.access_token
        } else {
            Write-Host "   ❌ $role login failed - no token received" -ForegroundColor Red
            return $null
        }
    } catch {
        Write-Host "   ❌ $role login error: $_" -ForegroundColor Red
        return $null
    }
}

function Test-OperationalPlan {
    param($token, $role, $message)
    
    Write-Host ""
    Write-Host "📋 Testing operational plan for $role..." -ForegroundColor Yellow
    Write-Host "   Query: '$message'" -ForegroundColor Gray
    
    try {
        $body = @{
            message = $message
            module = "nlp"
            clarification = $null
        } | ConvertTo-Json
        
        $headers = @{
            "Content-Type" = "application/json"
            "Authorization" = "Bearer $token"
        }
        
        $response = Invoke-RestMethod -Uri "$baseUrl/operational-ai/plan" -Method Post -Body $body -Headers $headers -UseBasicParsing
        
        Write-Host "   ✅ Plan created successfully" -ForegroundColor Green
        Write-Host "      Plan ID: $($response.plan_id)" -ForegroundColor Cyan
        Write-Host "      Intent: $($response.intent_type)" -ForegroundColor Cyan
        Write-Host "      Entity: $($response.entity)" -ForegroundColor Cyan
        Write-Host "      Risk Level: $($response.risk_level)" -ForegroundColor $(if ($response.risk_level -eq "LOW") { "Green" } elseif ($response.risk_level -eq "MEDIUM") { "Yellow" } else { "Red" })
        Write-Host "      Status: $($response.status)" -ForegroundColor Cyan
        Write-Host "      Confidence: $([math]::Round($response.confidence * 100, 2))%" -ForegroundColor Cyan
        Write-Host "      Impact: $($response.estimated_impact_count) records" -ForegroundColor Cyan
        
        if ($response.permission.allowed) {
            Write-Host "      Permission: ✅ Allowed" -ForegroundColor Green
        } else {
            Write-Host "      Permission: ❌ Denied - $($response.permission.reason)" -ForegroundColor Red
        }
        
        return $true
    } catch {
        $errorDetails = $_.ErrorDetails.Message | ConvertFrom-Json
        Write-Host "   ❌ Plan creation failed" -ForegroundColor Red
        Write-Host "      Error: $($errorDetails.detail)" -ForegroundColor Red
        return $false
    }
}

# Run Tests
Write-Host ""
Write-Host ("=" * 60)
Write-Host "TEST 1: ADMIN ACCESS" -ForegroundColor Magenta
Write-Host ("=" * 60)

$adminToken = Test-Login -email $adminCreds.email -password $adminCreds.password -role "ADMIN"

if ($adminToken) {
    # Test various admin operations
    Test-OperationalPlan -token $adminToken -role "ADMIN" -message "Show all students with CGPA below 6.0"
    Test-OperationalPlan -token $adminToken -role "ADMIN" -message "Update semester to 5 for students in section A"
    Test-OperationalPlan -token $adminToken -role "ADMIN" -message "Delete all students with admission year before 2020"
} else {
    Write-Host ""
    Write-Host "❌ Cannot proceed with admin tests - login failed" -ForegroundColor Red
}

Write-Host ""
Write-Host ("=" * 60)
Write-Host "TEST 2: FACULTY ACCESS" -ForegroundColor Magenta
Write-Host ("=" * 60)

$facultyToken = Test-Login -email $facultyCreds.email -password $facultyCreds.password -role "FACULTY"

if ($facultyToken) {
    # Test faculty operations
    Test-OperationalPlan -token $facultyToken -role "FACULTY" -message "Show all students in my department"
    Test-OperationalPlan -token $facultyToken -role "FACULTY" -message "Update student CS2101 CGPA to 7.5"
    Test-OperationalPlan -token $facultyToken -role "FACULTY" -message "Create attendance record for today class"
    Test-OperationalPlan -token $facultyToken -role "FACULTY" -message "Delete attendance record from yesterday"
    Test-OperationalPlan -token $facultyToken -role "FACULTY" -message "Update predicted grade to A for student CS2102"
} else {
    Write-Host ""
    Write-Host "❌ Cannot proceed with faculty tests - login failed" -ForegroundColor Red
}

Write-Host ""
Write-Host ("=" * 60)
Write-Host "TEST SUMMARY" -ForegroundColor Magenta
Write-Host ("=" * 60)
Write-Host ""
Write-Host "✅ Command Console testing complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To test manually:" -ForegroundColor Yellow
Write-Host "   1. Open http://localhost:5174" -ForegroundColor White
Write-Host "   2. Login with admin@campusiq.edu / admin123" -ForegroundColor White
Write-Host "   3. Navigate to Command Console (Terminal icon in sidebar)" -ForegroundColor White
Write-Host "   4. Try the example queries above" -ForegroundColor White
Write-Host "" 
