# Test CGPA Filtering Fix
$baseUrl = "http://localhost:8000"

Write-Host ""
Write-Host "Testing CGPA Filter Fix" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan

# Login as admin
Write-Host ""
Write-Host "Logging in as admin..." -ForegroundColor Yellow
$body = @{ email = "admin@campusiq.edu"; password = "admin123" } | ConvertTo-Json
$headers = @{ "Content-Type" = "application/json" }
$response = Invoke-RestMethod -Uri "$baseUrl/api/auth/login" -Method Post -Body $body -Headers $headers -UseBasicParsing
$token = $response.access_token

if ($token) {
    Write-Host "Login successful!" -ForegroundColor Green
    
    # Test CGPA below 7.0
    Write-Host ""
    Write-Host "Testing: 'Show all students with CGPA below 7.0'" -ForegroundColor Yellow
    
    $body = @{
        message = "Show all students with CGPA below 7.0"
        module = "nlp"
        clarification = $null
    } | ConvertTo-Json
    
    $headers = @{
        "Content-Type" = "application/json"
        "Authorization" = "Bearer $token"
    }
    
    try {
        $result = Invoke-RestMethod -Uri "$baseUrl/api/ops-ai/plan" -Method Post -Body $body -Headers $headers -UseBasicParsing
        
        Write-Host ""
        Write-Host "Results:" -ForegroundColor Cyan
        Write-Host "  Plan ID: $($result.plan_id)" -ForegroundColor White
        Write-Host "  Intent: $($result.intent_type)" -ForegroundColor White
        Write-Host "  Entity: $($result.entity)" -ForegroundColor White
        Write-Host "  Risk: $($result.risk_level)" -ForegroundColor White
        Write-Host "  Records found: $($result.estimated_impact_count)" -ForegroundColor White
        
        if ($result.preview -and $result.preview.affected_records) {
            Write-Host ""
            Write-Host "  Preview of affected students:" -ForegroundColor Yellow
            $result.preview.affected_records | Select-Object -First 5 | ForEach-Object {
                Write-Host "    Roll: $($_.roll_number), CGPA: $($_.cgpa)" -ForegroundColor White
            }
        }
        
        Write-Host ""
        Write-Host "Filters used:" -ForegroundColor Yellow
        Write-Host ($result.filters | ConvertTo-Json) -ForegroundColor Gray
        
        # Verify filters
        if ($result.filters.cgpa__lt -or $result.filters.cgpa_lt) {
            Write-Host ""
            Write-Host "SUCCESS: Filter correctly uses comparison operator (cgpa < 7.0)" -ForegroundColor Green
        } else {
            Write-Host ""
            Write-Host "WARNING: Filter might not be using comparison operator" -ForegroundColor Yellow
            Write-Host "Filter keys: $($result.filters.Keys -join ', ')" -ForegroundColor Gray
        }
        
    } catch {
        Write-Host "ERROR: $_" -ForegroundColor Red
    }
    
} else {
    Write-Host "Login failed!" -ForegroundColor Red
}

Write-Host ""
Write-Host "Test complete. Now try manually:" -ForegroundColor Cyan
Write-Host "  1. Open http://localhost:5174" -ForegroundColor White
Write-Host "  2. Login as admin@campusiq.edu / admin123" -ForegroundColor White
Write-Host "  3. Go to Command Console" -ForegroundColor White
Write-Host "  4. Type: Show all students with CGPA below 7.0" -ForegroundColor White
Write-Host "  5. Verify only students with CGPA < 7.0 are shown" -ForegroundColor White
Write-Host ""
