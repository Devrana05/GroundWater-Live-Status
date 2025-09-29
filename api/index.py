from fastapi import FastAPI
from mangum import Mangum

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Groundwater API is running"}

@app.get("/wells")
def get_wells():
    return [
        {"well_id": "ST001", "name": "Station 001", "current_level": 28.5, "status": "critical"},
        {"well_id": "ST002", "name": "Station 002", "current_level": 38.2, "status": "warning"},
        {"well_id": "ST003", "name": "Station 003", "current_level": 50.1, "status": "normal"}
    ]

@app.get("/dashboard/summary")
def get_dashboard_summary():
    return {
        "total_wells": 3,
        "active_wells": 3,
        "avg_current_level": 38.9,
        "active_alerts": 2
    }

@app.get("/alerts")
def get_alerts():
    return [
        {"id": 1, "well_id": "ST001", "severity": "critical", "message": "Critical water level"},
        {"id": 2, "well_id": "ST002", "severity": "warning", "message": "Low battery"}
    ]

handler = Mangum(app)