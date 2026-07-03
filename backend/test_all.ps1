Write-Host "`n=== SHUNDO FULL SYSTEM TEST ===`n" -ForegroundColor Cyan

function Test-Endpoint($name, $url, $method = "GET") {
    Write-Host "--- $name ---" -ForegroundColor Yellow
    try {
        $result = Invoke-RestMethod -Method $method -Uri $url
        $result | ConvertTo-Json -Depth 5
        Write-Host "[PASS] $name`n" -ForegroundColor Green
    } catch {
        Write-Host "[FAIL] $name : $($_.Exception.Message)`n" -ForegroundColor Red
    }
}

# Core infra
Test-Endpoint "Server Health" "http://localhost:8000/"
Test-Endpoint "Google Auth Status" "http://localhost:8000/auth/google/status"
Test-Endpoint "Calendar Read" "http://localhost:8000/test/calendar/events"

# Reflection loop
Test-Endpoint "Agent Reflection Loop" "http://localhost:8000/test/agent/run?goal=Schedule a 1 hour call tomorrow at 3 PM" "POST"

# New tools
Test-Endpoint "Places (OpenStreetMap)" "http://localhost:8000/test/places"
Test-Endpoint "Travel - Flights" "http://localhost:8000/test/travel/flights"
Test-Endpoint "Travel - Hotels" "http://localhost:8000/test/travel/hotels"
Test-Endpoint "Travel - Events" "http://localhost:8000/test/travel/events"
Test-Endpoint "Tasks" "http://localhost:8000/test/tasks"
Test-Endpoint "Notes" "http://localhost:8000/test/notes"
Test-Endpoint "Budget" "http://localhost:8000/test/budget"
Test-Endpoint "Weather" "http://localhost:8000/test/weather"
Test-Endpoint "Currency" "http://localhost:8000/test/currency"

Write-Host "`n=== TEST RUN COMPLETE ===`n" -ForegroundColor Cyan
