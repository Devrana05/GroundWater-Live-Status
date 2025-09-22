Write-Host "Starting Groundwater Monitoring System..." -ForegroundColor Green

# Check Docker
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker not found! Install Docker Desktop." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check Docker Compose
if (!(Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "Docker Compose not found!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Building and starting services..." -ForegroundColor Yellow
docker-compose up -d --build

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "Groundwater Monitoring System Started!" -ForegroundColor Green
    Write-Host "========================================`n" -ForegroundColor Green
    
    Write-Host "Web Dashboard: http://localhost" -ForegroundColor Cyan
    Write-Host "Mobile Interface: http://mobile.localhost" -ForegroundColor Cyan
    Write-Host "API Docs: http://localhost/api/docs" -ForegroundColor Cyan
    Write-Host "Grafana: http://localhost:3002 (admin/admin)" -ForegroundColor Cyan
    Write-Host "`nLogin: admin / admin123`n" -ForegroundColor Yellow
    
    Write-Host "Services Status:" -ForegroundColor White
    docker-compose ps
    
    Write-Host "`nPress Ctrl+C to stop logs..." -ForegroundColor Gray
    docker-compose logs -f
} else {
    Write-Host "Failed to start services!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
}