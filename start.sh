#!/bin/bash

echo "Starting Groundwater Monitoring System..."

# Check if Docker is running
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed or not running!"
    echo "Please install Docker and start it."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not available!"
    echo "Please install Docker Compose."
    exit 1
fi

echo "Building and starting services..."
docker-compose up -d --build

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "Groundwater Monitoring System Started!"
    echo "========================================"
    echo ""
    echo "Web Interface: http://localhost"
    echo "Mobile Interface: http://mobile.localhost"
    echo "API Documentation: http://localhost/api/docs"
    echo "Mobile API: http://mobile.localhost/api/docs"
    echo "Grafana Dashboard: http://localhost:3002"
    echo "Prometheus: http://localhost:9090"
    echo ""
    echo "Services Status:"
    docker-compose ps
    echo ""
    echo "Press Ctrl+C to stop viewing logs..."
    docker-compose logs -f
else
    echo "Failed to start services!"
    echo "Check the error messages above."
    exit 1
fi