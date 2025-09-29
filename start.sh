#!/bin/bash
echo "Starting Groundwater Monitoring System..."

# Start FastAPI backend
echo "Starting API server..."
cd services/api
pip install fastapi uvicorn --quiet
python main.py &
API_PID=$!
cd ../..

# Wait for API to start
sleep 3

# Start frontend server
echo "Starting frontend server..."
python -m http.server 8080 &
FRONTEND_PID=$!

# Wait a moment then open browser
sleep 2
echo "Opening browser..."
if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:8080
elif command -v open > /dev/null; then
    open http://localhost:8080
fi

echo "System started successfully!"
echo "Frontend: http://localhost:8080"
echo "API: http://localhost:8000"
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap "kill $API_PID $FRONTEND_PID; exit" INT
wait