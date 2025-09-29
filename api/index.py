from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        if self.path == '/api/wells':
            data = [
                {"well_id": "ST001", "name": "Station 001", "current_level": 28.5, "status": "critical"},
                {"well_id": "ST002", "name": "Station 002", "current_level": 38.2, "status": "warning"},
                {"well_id": "ST003", "name": "Station 003", "current_level": 50.1, "status": "normal"}
            ]
        elif self.path == '/api/dashboard/summary':
            data = {
                "total_wells": 3,
                "active_wells": 3,
                "avg_current_level": 38.9,
                "active_alerts": 2
            }
        elif self.path == '/api/alerts':
            data = [
                {"id": 1, "well_id": "ST001", "severity": "critical", "message": "Critical water level"},
                {"id": 2, "well_id": "ST002", "severity": "warning", "message": "Low battery"}
            ]
        else:
            data = {"message": "Groundwater API is running"}
        
        self.wfile.write(json.dumps(data).encode())