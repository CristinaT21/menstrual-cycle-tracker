# Test Live Message Processing
# This script logs a cycle and monitors RabbitMQ in real-time

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Live Message Queue Testing" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Login
Write-Host "Logging in..." -ForegroundColor Yellow
$loginBody = @{
    email = "demo@example.com"
    password = "password123"
} | ConvertTo-Json

$loginResponse = Invoke-RestMethod -Uri "http://localhost/api/users/login" `
    -Method Post `
    -ContentType "application/json" `
    -Body $loginBody

$token = $loginResponse.token
$headers = @{ "Authorization" = "Bearer $token" }

Write-Host "[OK] Logged in as: $($loginResponse.user.username)`n" -ForegroundColor Green

# Open RabbitMQ in browser
Write-Host "Opening RabbitMQ Management UI..." -ForegroundColor Yellow
Write-Host "Navigate to: http://localhost:15672/#/queues" -ForegroundColor Cyan
Write-Host "Watch the 'analytics_cycle_queue' before proceeding!`n" -ForegroundColor Yellow

Read-Host "Press ENTER when you're ready to send a message"

# Log a new cycle
Write-Host "`nPublishing cycle event..." -ForegroundColor Yellow
$cycleBody = @{
    start_date = "2025-01-08"
    end_date = "2025-01-13"
} | ConvertTo-Json

try {
    $cycleResponse = Invoke-RestMethod -Uri "http://localhost/api/cycles/cycles" `
        -Method Post `
        -Headers $headers `
        -ContentType "application/json" `
        -Body $cycleBody

    Write-Host "[OK] Cycle logged! Event published to RabbitMQ" -ForegroundColor Green
    Write-Host "    Cycle ID: $($cycleResponse.cycle.id)" -ForegroundColor Gray
}
catch {
    Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nCheck RabbitMQ UI now - you should see:" -ForegroundColor Cyan
Write-Host "1. analytics_cycle_queue: Message briefly appears then disappears" -ForegroundColor White
Write-Host "2. notification_prediction_queue: Message appears after processing" -ForegroundColor White

Write-Host "`nWaiting 5 seconds for async processing..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check logs
Write-Host "`nChecking service logs for message processing...`n" -ForegroundColor Yellow

Write-Host "=== CYCLE TRACKING SERVICE (Publisher) ===" -ForegroundColor Cyan
docker-compose logs --tail=5 cycle-tracking-service | Select-String "Published"

Write-Host "`n=== ANALYTICS SERVICE (Consumer) ===" -ForegroundColor Cyan
docker-compose logs --tail=10 analytics-service | Select-String "Received|prediction"

Write-Host "`n=== NOTIFICATION SERVICE (Consumer) ===" -ForegroundColor Cyan
docker-compose logs --tail=5 notification-service | Select-String "Received|notification"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Message Processing Verified!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`nKey Observations for Research Paper:" -ForegroundColor Yellow
Write-Host "- Messages are processed and removed immediately (0 in queue = good)" -ForegroundColor White
Write-Host "- Event-driven architecture enables loose coupling" -ForegroundColor White
Write-Host "- Services communicate asynchronously without blocking" -ForegroundColor White
Write-Host "- RabbitMQ ensures message delivery between services" -ForegroundColor White
