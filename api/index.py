from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        path = urlparse(self.path).path
        
        if path == '/wells':
            data = [
                {"well_id": "ST001", "name": "Station 001", "latitude": 28.6139, "longitude": 77.2090, "current_level": 45.2, "status": "normal"},
                {"well_id": "ST002", "name": "Station 002", "latitude": 28.6129, "longitude": 77.2290, "current_level": 32.1, "status": "warning"},
                {"well_id": "ST003", "name": "Station 003", "latitude": 28.6149, "longitude": 77.1990, "current_level": 18.5, "status": "critical"}
            ]
        elif path == '/dashboard/summary':
            data = {
                "total_wells": 3,
                "active_wells": 3,
                "avg_current_level": 31.9,
                "active_alerts": 2,
                "avg_24h_change": -1.2
            }
        elif path == '/alerts':
            data = [
                {"id": 1, "well_id": "ST001", "severity": "critical", "message": "Critical water level", "created_at": datetime.now().isoformat()},
                {"id": 2, "well_id": "ST002", "severity": "warning", "message": "Low battery", "created_at": datetime.now().isoformat()}
            ]
        elif path.startswith('/wells/') and path.endswith('/timeseries'):
            now = datetime.now()
            data = []
            for i in range(24):
                timestamp = now - timedelta(hours=i)
                level = 45.2 - (i * 0.5) + (i % 3)
                data.append({
                    "bucket": timestamp.isoformat(),
                    "avg_level": level,
                    "min_level": level - 1,
                    "max_level": level + 1
                })
            data = list(reversed(data))
        else:
            data = {"message": "Groundwater API is running"}
        
        self.wfile.write(json.dumps(data).encode())
    
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        if self.path == '/auth/login':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            user_data = json.loads(post_data.decode('utf-8'))
            
            if user_data.get('username') == 'admin' and user_data.get('password') == 'admin123':
                data = {
                    "access_token": "demo_token",
                    "token_type": "bearer",
                    "user": {"username": "admin", "full_name": "Administrator", "role": "admin"}
                }
            else:
                self.send_response(401)
                data = {"detail": "Invalid credentials"}
        else:
            data = {"message": "Not found"}
        
        self.wfile.write(json.dumps(data).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()