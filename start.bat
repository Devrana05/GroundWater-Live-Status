@echo off
echo Starting Groundwater Monitoring System...

REM Check if Docker is running
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker is not installed or not running!
    echo Please install Docker Desktop and start it.
    pause
    exit /b 1
)

REM Check if docker-compose is available
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker Compose is not available!
    echo Please install Docker Compose.
    pause
    exit /b 1
)

echo Building and starting services...
docker-compose up -d --build

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo Groundwater Monitoring System Started!
    echo ========================================
    echo.
    echo Web Interface: http://localhost
    echo Mobile Interface: http://mobile.localhost
    echo API Documentation: http://localhost/api/docs
    echo Mobile API: http://mobile.localhost/api/docs
    echo Grafana Dashboard: http://localhost:3002
    echo Prometheus: http://localhost:9090
    echo.
    echo Services Status:
    docker-compose ps
    echo.
    echo Press any key to view logs or Ctrl+C to exit...
    pause >nul
    docker-compose logs -f
) else (
    echo Failed to start services!
    echo Check the error messages above.
    pause
)