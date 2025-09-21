from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional
import asyncio
import redis

app = FastAPI(title="Groundwater Monitoring API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/groundwater")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Redis client for caching
redis_client = redis.from_url(REDIS_URL)

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                self.disconnect(connection)

manager = ConnectionManager()

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

@app.get("/wells")
async def get_wells():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT w.*, 
                   m.water_level as current_level,
                   m.time as last_reading,
                   m.battery_level,
                   m.device_status
            FROM wells w
            LEFT JOIN LATERAL (
                SELECT * FROM measurements_clean 
                WHERE well_id = w.well_id 
                ORDER BY time DESC LIMIT 1
            ) m ON true
            WHERE w.status = 'active'
        """)
        
        wells = cur.fetchall()
        cur.close()
        conn.close()
        
        return [dict(well) for well in wells]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/wells/{well_id}/timeseries")
async def get_well_timeseries(
    well_id: str, 
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    interval: str = "1h"
):
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now().isoformat()
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).isoformat()
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                time_bucket(%s, time) as bucket,
                AVG(water_level) as avg_level,
                MIN(water_level) as min_level,
                MAX(water_level) as max_level,
                AVG(battery_level) as avg_battery,
                COUNT(*) as reading_count
            FROM measurements_clean
            WHERE well_id = %s 
            AND time BETWEEN %s AND %s
            GROUP BY bucket
            ORDER BY bucket
        """, (interval, well_id, start_date, end_date))
        
        data = cur.fetchall()
        cur.close()
        conn.close()
        
        return [dict(row) for row in data]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/wells/{well_id}/forecast")
async def get_well_forecast(well_id: str, days: int = 7):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT forecast_time, predicted_level, confidence_lower, confidence_upper
            FROM forecasts
            WHERE well_id = %s 
            AND forecast_time > NOW()
            AND forecast_time <= NOW() + INTERVAL '%s days'
            ORDER BY forecast_time
        """, (well_id, days))
        
        forecasts = cur.fetchall()
        cur.close()
        conn.close()
        
        return [dict(forecast) for forecast in forecasts]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alerts")
async def get_alerts(active_only: bool = True):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        query = """
            SELECT a.*, w.name as well_name
            FROM alerts a
            JOIN wells w ON a.well_id = w.well_id
        """
        
        if active_only:
            query += " WHERE a.is_active = true"
        
        query += " ORDER BY a.created_at DESC LIMIT 50"
        
        cur.execute(query)
        alerts = cur.fetchall()
        cur.close()
        conn.close()
        
        return [dict(alert) for alert in alerts]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard/summary")
async def get_dashboard_summary():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get summary statistics
        cur.execute("""
            WITH latest_readings AS (
                SELECT DISTINCT ON (well_id) 
                    well_id, water_level, time
                FROM measurements_clean
                ORDER BY well_id, time DESC
            ),
            previous_readings AS (
                SELECT DISTINCT ON (well_id)
                    well_id, water_level
                FROM measurements_clean
                WHERE time < NOW() - INTERVAL '24 hours'
                ORDER BY well_id, time DESC
            )
            SELECT 
                COUNT(DISTINCT w.well_id) as total_wells,
                AVG(lr.water_level) as avg_current_level,
                COUNT(CASE WHEN w.status = 'active' THEN 1 END) as active_wells,
                COUNT(CASE WHEN a.is_active THEN 1 END) as active_alerts,
                AVG(lr.water_level - pr.water_level) as avg_24h_change
            FROM wells w
            LEFT JOIN latest_readings lr ON w.well_id = lr.well_id
            LEFT JOIN previous_readings pr ON w.well_id = pr.well_id
            LEFT JOIN alerts a ON w.well_id = a.well_id AND a.is_active = true
        """)
        
        summary = dict(cur.fetchone())
        cur.close()
        conn.close()
        
        return summary
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Send real-time updates every 30 seconds
            await asyncio.sleep(30)
            
            # Get latest data
            conn = get_db_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT well_id, water_level, battery_level, time
                FROM measurements_clean
                WHERE time > NOW() - INTERVAL '5 minutes'
                ORDER BY time DESC
            """)
            
            recent_data = [dict(row) for row in cur.fetchall()]
            cur.close()
            conn.close()
            
            await websocket.send_text(json.dumps({
                "type": "real_time_update",
                "data": recent_data,
                "timestamp": datetime.now().isoformat()
            }))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)