#!/usr/bin/env python3
"""
Test data generator for DWLR system
Generates realistic groundwater level data and sends via MQTT/HTTP
"""

import json
import time
import random
import requests
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
import argparse
import threading

class DWLRDataGenerator:
    def __init__(self, mqtt_host='localhost', api_url='http://localhost:8001'):
        self.mqtt_host = mqtt_host
        self.api_url = api_url
        self.mqtt_client = None
        
        # Well configurations
        self.wells = {
            'ST001': {
                'base_level': 18.5,
                'variance': 2.0,
                'trend': -0.01,  # Declining trend
                'lat': 28.6139,
                'lon': 77.2090
            },
            'ST002': {
                'base_level': 42.1,
                'variance': 1.5,
                'trend': 0.005,  # Slight increase
                'lat': 28.6289,
                'lon': 77.2194
            },
            'ST003': {
                'base_level': 35.8,
                'variance': 2.5,
                'trend': -0.02,  # Declining trend
                'lat': 28.6089,
                'lon': 77.1986
            }
        }
        
        # Current state
        self.current_levels = {well: config['base_level'] for well, config in self.wells.items()}
        self.battery_levels = {well: random.uniform(80, 100) for well in self.wells.keys()}
    
    def setup_mqtt(self):
        """Setup MQTT client"""
        try:
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.connect(self.mqtt_host, 1883, 60)
            self.mqtt_client.loop_start()
            print(f"Connected to MQTT broker at {self.mqtt_host}")
            return True
        except Exception as e:
            print(f"MQTT connection failed: {e}")
            return False
    
    def generate_reading(self, well_id):
        """Generate realistic reading for a well"""
        config = self.wells[well_id]
        
        # Apply trend and random variation
        trend_change = config['trend'] * random.uniform(0.5, 1.5)
        random_change = random.gauss(0, config['variance'] * 0.1)
        
        # Update current level
        self.current_levels[well_id] += trend_change + random_change
        
        # Ensure reasonable bounds
        self.current_levels[well_id] = max(5.0, min(100.0, self.current_levels[well_id]))
        
        # Battery drain simulation
        self.battery_levels[well_id] -= random.uniform(0.01, 0.05)
        if self.battery_levels[well_id] < 10:
            self.battery_levels[well_id] = random.uniform(90, 100)  # Battery replaced
        
        # Generate reading
        reading = {
            'well_id': well_id,
            'timestamp': datetime.now().isoformat(),
            'water_level': round(self.current_levels[well_id], 2),
            'battery_level': round(self.battery_levels[well_id], 1),
            'temperature': round(random.uniform(18, 28), 1),
            'latitude': config['lat'],
            'longitude': config['lon'],
            'device_status': 'online' if random.random() > 0.05 else 'warning'
        }
        
        return reading
    
    def send_mqtt_reading(self, well_id, reading):
        """Send reading via MQTT"""
        if not self.mqtt_client:
            return False
        
        try:
            topic = f"dwlr/{well_id}/data"
            payload = json.dumps(reading)
            self.mqtt_client.publish(topic, payload)
            return True
        except Exception as e:
            print(f"MQTT send error: {e}")
            return False
    
    def send_http_reading(self, reading):
        """Send reading via HTTP API"""
        try:
            response = requests.post(
                f"{self.api_url}/ingest/dwlr",
                json=reading,
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            print(f"HTTP send error: {e}")
            return False
    
    def generate_historical_data(self, days=30):
        """Generate historical data for the past N days"""
        print(f"Generating {days} days of historical data...")
        
        start_time = datetime.now() - timedelta(days=days)
        
        for well_id in self.wells.keys():
            # Reset to base level for historical generation
            self.current_levels[well_id] = self.wells[well_id]['base_level']
            
            current_time = start_time
            while current_time < datetime.now():
                reading = self.generate_reading(well_id)
                reading['timestamp'] = current_time.isoformat()
                
                # Send via HTTP (more reliable for bulk data)
                success = self.send_http_reading(reading)
                if success:
                    print(f"✓ {well_id} @ {current_time.strftime('%Y-%m-%d %H:%M')}")
                else:
                    print(f"✗ Failed: {well_id} @ {current_time.strftime('%Y-%m-%d %H:%M')}")
                
                # Increment time (15-minute intervals)
                current_time += timedelta(minutes=15)
                
                # Small delay to avoid overwhelming the system
                time.sleep(0.1)
    
    def run_real_time_simulation(self, interval=30):
        """Run continuous real-time data generation"""
        print(f"Starting real-time simulation (interval: {interval}s)")
        
        # Setup MQTT
        mqtt_connected = self.setup_mqtt()
        
        try:
            while True:
                for well_id in self.wells.keys():
                    reading = self.generate_reading(well_id)
                    
                    # Try MQTT first, fallback to HTTP
                    if mqtt_connected:
                        mqtt_success = self.send_mqtt_reading(well_id, reading)
                        if mqtt_success:
                            print(f"📡 MQTT: {well_id} - {reading['water_level']}m")
                        else:
                            # Fallback to HTTP
                            http_success = self.send_http_reading(reading)
                            if http_success:
                                print(f"🌐 HTTP: {well_id} - {reading['water_level']}m")
                            else:
                                print(f"❌ Failed: {well_id}")
                    else:
                        # HTTP only
                        http_success = self.send_http_reading(reading)
                        if http_success:
                            print(f"🌐 HTTP: {well_id} - {reading['water_level']}m")
                        else:
                            print(f"❌ Failed: {well_id}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nStopping simulation...")
        finally:
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
    
    def generate_anomaly_data(self):
        """Generate some anomalous readings for testing alerts"""
        print("Generating anomaly data for testing...")
        
        anomalies = [
            # Critical low level
            {'well_id': 'ST001', 'water_level': 15.0, 'type': 'critical_low'},
            # Rapid change
            {'well_id': 'ST002', 'water_level': 35.0, 'type': 'rapid_change'},
            # Low battery
            {'well_id': 'ST003', 'battery_level': 15.0, 'type': 'low_battery'}
        ]
        
        for anomaly in anomalies:
            well_id = anomaly['well_id']
            reading = self.generate_reading(well_id)
            
            # Apply anomaly
            if 'water_level' in anomaly:
                reading['water_level'] = anomaly['water_level']
            if 'battery_level' in anomaly:
                reading['battery_level'] = anomaly['battery_level']
            
            # Send reading
            success = self.send_http_reading(reading)
            if success:
                print(f"🚨 Anomaly sent: {well_id} - {anomaly['type']}")
            else:
                print(f"❌ Failed to send anomaly: {well_id}")
            
            time.sleep(2)

def main():
    parser = argparse.ArgumentParser(description='DWLR Test Data Generator')
    parser.add_argument('--mode', choices=['historical', 'realtime', 'anomaly'], 
                       default='realtime', help='Generation mode')
    parser.add_argument('--days', type=int, default=7, 
                       help='Days of historical data to generate')
    parser.add_argument('--interval', type=int, default=30, 
                       help='Real-time interval in seconds')
    parser.add_argument('--mqtt-host', default='localhost', 
                       help='MQTT broker host')
    parser.add_argument('--api-url', default='http://localhost:8001', 
                       help='API base URL')
    
    args = parser.parse_args()
    
    generator = DWLRDataGenerator(
        mqtt_host=args.mqtt_host,
        api_url=args.api_url
    )
    
    if args.mode == 'historical':
        generator.generate_historical_data(args.days)
    elif args.mode == 'realtime':
        generator.run_real_time_simulation(args.interval)
    elif args.mode == 'anomaly':
        generator.generate_anomaly_data()

if __name__ == "__main__":
    main()