from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import json

app = FastAPI(title="Groundwater Monitoring API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserLogin(BaseModel):
    username: str
    password: str

@app.post("/auth/login")
async def login(user_data: UserLogin):
    if user_data.username == 'admin' and user_data.password == 'admin123':
        return {
            "access_token": "demo_token",
            "token_type": "bearer",
            "user": {"username": "admin", "full_name": "Administrator", "role": "admin"}
        }
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/wells")
async def get_wells():
    return [
        {"well_id": "ST001", "name": "Station 001", "latitude": 28.6139, "longitude": 77.2090, "current_level": 45.2, "status": "normal"},
        {"well_id": "ST002", "name": "Station 002", "latitude": 28.6129, "longitude": 77.2290, "current_level": 32.1, "status": "warning"},
        {"well_id": "ST003", "name": "Station 003", "latitude": 28.6149, "longitude": 77.1990, "current_level": 18.5, "status": "critical"}
    ]

@app.get("/dashboard/summary")
async def get_dashboard_summary():
    return {
        "total_wells": 3,
        "active_wells": 3,
        "avg_current_level": 31.9,
        "active_alerts": 2,
        "avg_24h_change": -1.2
    }

@app.get("/alerts")
async def get_alerts():
    return [
        {"id": 1, "well_id": "ST001", "severity": "critical", "message": "Critical water level", "created_at": datetime.now().isoformat()},
        {"id": 2, "well_id": "ST002", "severity": "warning", "message": "Low battery", "created_at": datetime.now().isoformat()}
    ]

@app.get("/wells/{well_id}/timeseries")
async def get_well_timeseries(well_id: str):
    # Generate sample time series data
    now = datetime.now()
    data = []
    for i in range(24):
        timestamp = now - timedelta(hours=i)
        level = 45.2 - (i * 0.5) + (i % 3)  # Sample declining trend with variation
        data.append({
            "bucket": timestamp.isoformat(),
            "avg_level": level,
            "min_level": level - 1,
            "max_level": level + 1
        })
    return list(reversed(data))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)