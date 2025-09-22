import json
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from kafka import KafkaConsumer
import redis
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/groundwater")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Initialize connections
redis_client = redis.from_url(REDIS_URL)

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def validate_measurement(data):
    """Validate and clean measurement data"""
    try:
        # Basic validation
        if not all(key in data for key in ['well_id', 'timestamp', 'water_level']):
            return None, 0.0
        
        # Range validation
        water_level = float(data['water_level'])
        if water_level < 0 or water_level > 100:  # Reasonable range
            return None, 0.0
        
        # Battery level validation
        battery_level = data.get('battery_level')
        if battery_level is not None:
            battery_level = float(battery_level)
            if battery_level < 0 or battery_level > 100:
                battery_level = None
        
        # Temperature validation
        temperature = data.get('temperature')
        if temperature is not None:
            temperature = float(temperature)
            if temperature < -50 or temperature > 80:  # Reasonable range
                temperature = None
        
        cleaned_data = {
            'well_id': data['well_id'],
            'timestamp': data['timestamp'],
            'water_level': water_level,
            'battery_level': battery_level,
            'temperature': temperature,
            'device_status': data.get('device_status', 'online')
        }
        
        # Calculate quality score based on completeness and reasonableness
        quality_score = 0.8  # Base score
        if battery_level is not None:
            quality_score += 0.1
        if temperature is not None:
            quality_score += 0.1
        
        return cleaned_data, quality_score
    
    except Exception as e:
        print(f"Validation error: {e}")
        return None, 0.0

def detect_anomalies(well_id, water_level):
    """Simple anomaly detection using historical data"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get recent measurements for comparison
        cur.execute("""
            SELECT water_level 
            FROM measurements_clean 
            WHERE well_id = %s 
            AND time > NOW() - INTERVAL '24 hours'
            ORDER BY time DESC 
            LIMIT 10
        """, (well_id,))
        
        recent_levels = [row['water_level'] for row in cur.fetchall()]
        cur.close()
        conn.close()
        
        if len(recent_levels) < 3:
            return False  # Not enough data
        
        # Simple statistical anomaly detection
        mean_level = np.mean(recent_levels)
        std_level = np.std(recent_levels)
        
        # Flag as anomaly if more than 2 standard deviations away
        return abs(water_level - mean_level) > 2 * std_level
    
    except Exception as e:
        print(f"Anomaly detection error: {e}")
        return False

def process_measurement(data):
    """Process and store cleaned measurement"""
    try:
        cleaned_data, quality_score = validate_measurement(data)
        
        if cleaned_data is None:
            print(f"Invalid measurement data: {data}")
            return False
        
        # Check for anomalies
        is_anomaly = detect_anomalies(cleaned_data['well_id'], cleaned_data['water_level'])
        
        if is_anomaly:
            print(f"Anomaly detected for well {cleaned_data['well_id']}: {cleaned_data['water_level']}")
            # Could trigger alert here
        
        # Store in clean measurements table
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO measurements_clean 
            (time, well_id, water_level, battery_level, temperature, device_status, quality_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            cleaned_data['timestamp'],
            cleaned_data['well_id'],
            cleaned_data['water_level'],
            cleaned_data['battery_level'],
            cleaned_data['temperature'],
            cleaned_data['device_status'],
            quality_score
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        # Update cache
        cache_key = f"latest:{cleaned_data['well_id']}"
        redis_client.setex(cache_key, 3600, json.dumps(cleaned_data, default=str))
        
        print(f"Processed measurement for well {cleaned_data['well_id']}")
        return True
    
    except Exception as e:
        print(f"Processing error: {e}")
        return False

def check_alert_conditions(well_id, water_level):
    """Check if measurement triggers any alerts"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get well thresholds
        cur.execute("""
            SELECT critical_level, warning_level 
            FROM wells 
            WHERE well_id = %s
        """, (well_id,))
        
        well = cur.fetchone()
        if not well:
            return
        
        # Check for critical level
        if water_level <= well['critical_level']:
            cur.execute("""
                INSERT INTO alerts (well_id, alert_type, severity, message, threshold_value, current_value)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                well_id,
                'critical_water_level',
                'critical',
                f'Water level critically low: {water_level}m',
                well['critical_level'],
                water_level
            ))
        
        # Check for warning level
        elif water_level <= well['warning_level']:
            cur.execute("""
                INSERT INTO alerts (well_id, alert_type, severity, message, threshold_value, current_value)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                well_id,
                'low_water_level',
                'warning',
                f'Water level below warning threshold: {water_level}m',
                well['warning_level'],
                water_level
            ))
        
        conn.commit()
        cur.close()
        conn.close()
    
    except Exception as e:
        print(f"Alert check error: {e}")

def main():
    """Main ETL processing loop"""
    print("Starting ETL processor...")
    
    # Initialize Kafka consumer
    consumer = KafkaConsumer(
        'dwlr_readings',
        bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
        value_deserializer=lambda x: json.loads(x.decode('utf-8')),
        group_id='etl_processor'
    )
    
    print("Listening for messages...")
    
    for message in consumer:
        try:
            data = message.value
            print(f"Processing message: {data}")
            
            # Process the measurement
            if process_measurement(data):
                # Check for alert conditions
                check_alert_conditions(data['well_id'], data['water_level'])
            
        except Exception as e:
            print(f"Message processing error: {e}")
            continue

if __name__ == "__main__":
    main()