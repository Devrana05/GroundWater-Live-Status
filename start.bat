@echo off
echo Starting Groundwater Monitoring System...

REM Start FastAPI backend
echo Starting API server...
start "API Server" cmd /k "cd services\api && python -m pip install fastapi uvicorn --quiet && python main.py"

REM Wait for API to start
timeout /t 3 /nobreak >nul

REM Start frontend server
echo Starting frontend server...
start "Frontend Server" cmd /k "python -m http.server 8080"

REM Wait a moment then open browser
timeout /t 2 /nobreak >nul
echo Opening browser...
start http://localhost:8080

echo System started successfully!
echo Frontend: http://localhost:8080
echo API: http://localhost:8000
pause