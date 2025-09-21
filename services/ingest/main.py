from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import json
import os
from datetime import datetime
from kafka import KafkaProducer
import paho.mqtt.client as mqtt
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI(title="DWLR Data Ingestion Service")

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/groundwater")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")

# Kafka producer
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)

class DWLRReading(BaseModel):
    well_id: str
    timestamp: datetime
    water_level: float
    battery_level: float = None
    temperature: float = None
    latitude: float = None
    longitude: float = None
    device_status: str = "online"

def validate_reading(data: dict) -> bool:
    required_fields = ['well_id', 'timestamp', 'water_level']
    return all(field in data for field in required_fields)

def store_raw_data(reading: dict):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO measurements_raw 
            (time, well_id, water_level, battery_level, temperature, device_status, raw_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            reading['timestamp'],
            reading['well_id'],
            reading['water_level'],
            reading.get('battery_level'),
            reading.get('temperature'),
            reading.get('device_status', 'online'),
            json.dumps(reading)
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Database error: {e}")
        return False

@app.post("/ingest/dwlr")
async def ingest_dwlr_data(reading: DWLRReading):
    try:
        reading_dict = reading.dict()
        
        # Validate data
        if not validate_reading(reading_dict):
            raise HTTPException(status_code=400, detail="Invalid reading data")
        
        # Store raw data
        if not store_raw_data(reading_dict):
            raise HTTPException(status_code=500, detail="Failed to store data")
        
        # Publish to Kafka for processing
        producer.send('dwlr_readings', reading_dict)
        
        return {"status": "success", "message": "Data ingested successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# MQTT Client Setup
def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker with result code {rc}")
    client.subscribe("dwlr/+/data")

def on_message(client, userdata, msg):
    try:
        topic_parts = msg.topic.split('/')
        well_id = topic_parts[1]
        
        data = json.loads(msg.payload.decode())
        data['well_id'] = well_id
        data['timestamp'] = datetime.now().isoformat()
        
        if validate_reading(data):
            store_raw_data(data)
            producer.send('dwlr_readings', data)
            print(f"Processed MQTT data for well {well_id}")
        
    except Exception as e:
        print(f"MQTT processing error: {e}")

# Initialize MQTT client
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

@app.on_event("startup")
async def startup_event():
    try:
        mqtt_client.connect(MQTT_BROKER, 1883, 60)
        mqtt_client.loop_start()
        print("MQTT client started")
    except Exception as e:
        print(f"MQTT connection failed: {e}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ingest"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)