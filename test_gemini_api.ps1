# Test Gemini API Integration
# Quick verification script to ensure API is configured correctly

param(
    [string]$ApiKey = $env:GOOGLE_API_KEY
)

Write-Host "🧪 Testing Gemini API Integration..." -ForegroundColor Cyan
Write-Host ""

# Check if API key is set
if (-not $ApiKey) {
    Write-Host "❌ GOOGLE_API_KEY not set!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please set your API key:" -ForegroundColor Yellow
    Write-Host '  $env:GOOGLE_API_KEY = "AIzaSy_YOUR_KEY_HERE"' -ForegroundColor White
    Write-Host ""
    Write-Host "Or add it to .env file:" -ForegroundColor Yellow
    Write-Host "  GOOGLE_API_KEY=AIzaSy_YOUR_KEY_HERE" -ForegroundColor White
    Write-Host ""
    Write-Host "Get your FREE API key at:" -ForegroundColor Yellow
    Write-Host "  https://aistudio.google.com/app/apikey" -ForegroundColor Cyan
    exit 1
}

# Mask API key for display
$MaskedKey = $ApiKey.Substring(0, [Math]::Min(10, $ApiKey.Length)) + "..." + $ApiKey.Substring([Math]::Max(0, $ApiKey.Length - 4))
Write-Host "✓ API Key found: $MaskedKey" -ForegroundColor Green
Write-Host ""

# Test API endpoint
Write-Host "Testing connection to Gemini API..." -ForegroundColor Yellow

$endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=$ApiKey"
$payload = @{
    contents = @(
        @{
            role = "user"
            parts = @(
                @{ text = "Say 'Hello from CampusIQ!' in exactly 5 words." }
            )
        }
    )
    generationConfig = @{
        temperature = 0.1
        maxOutputTokens = 50
    }
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri $endpoint -Method Post -Body $payload -ContentType "application/json" -TimeoutSec 15
    
    if ($response.candidates) {
        $text = $response.candidates[0].content.parts[0].text
        Write-Host ""
        Write-Host "✅ SUCCESS! Gemini API is working!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Response from Gemini:" -ForegroundColor Cyan
        Write-Host "  `"$text`"" -ForegroundColor White
        Write-Host ""
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
        Write-Host "✅ CampusIQ is ready to use Gemini API!" -ForegroundColor Green
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Cyan
        Write-Host "1. Start the server: .\start_production.ps1" -ForegroundColor White
        Write-Host "2. Open API docs: http://localhost:8000/docs" -ForegroundColor White
        Write-Host "3. Test chatbot endpoint in the docs" -ForegroundColor White
        Write-Host ""
    } else {
        Write-Host "⚠️  API returned no candidates" -ForegroundColor Yellow
        Write-Host "Response: $($response | ConvertTo-Json)" -ForegroundColor Gray
    }
} catch {
    Write-Host ""
    Write-Host "❌ API Test Failed!" -ForegroundColor Red
    Write-Host ""
    
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "Status Code: $statusCode" -ForegroundColor Yellow
        
        switch ($statusCode) {
            400 {
                Write-Host "Error: Bad Request - Check API key format" -ForegroundColor Red
            }
            401 {
                Write-Host "Error: Unauthorized - Invalid API key" -ForegroundColor Red
                Write-Host ""
                Write-Host "💡 Solutions:" -ForegroundColor Yellow
                Write-Host "  1. Verify your API key at: https://aistudio.google.com/app/apikey" -ForegroundColor White
                Write-Host "  2. Generate a new key if needed" -ForegroundColor White
                Write-Host "  3. Update your .env file" -ForegroundColor White
            }
            403 {
                Write-Host "Error: Forbidden - API key may be restricted" -ForegroundColor Red
            }
            429 {
                Write-Host "Error: Rate Limited - Too many requests" -ForegroundColor Red
                Write-Host ""
                Write-Host "💡 Solutions:" -ForegroundColor Yellow
                Write-Host "  1. Wait 60 seconds and try again" -ForegroundColor White
                Write-Host "  2. Get additional API keys for key pooling" -ForegroundColor White
            }
            500 {
                Write-Host "Error: Server Error - Gemini API issue" -ForegroundColor Red
                Write-Host "Try again in a few minutes" -ForegroundColor Yellow
            }
            default {
                Write-Host "Error: HTTP $statusCode" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        Write-Host "💡 Possible causes:" -ForegroundColor Yellow
        Write-Host "  - No internet connection" -ForegroundColor White
        Write-Host "  - Firewall blocking requests" -ForegroundColor White
        Write-Host "  - Proxy configuration needed" -ForegroundColor White
    }
    
    Write-Host ""
    Write-Host "📖 See GEMINI_API_SETUP.md for detailed troubleshooting" -ForegroundColor Cyan
    exit 1
}

Write-Host ""
