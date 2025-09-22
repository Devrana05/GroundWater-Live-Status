import json
import time
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import psycopg2
from psycopg2.extras import RealDictCursor
from kafka import KafkaConsumer
import os
from datetime import datetime, timedelta

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/groundwater")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

class AlertEngine:
    def __init__(self):
        self.alert_cooldown = {}  # Prevent spam alerts
    
    def send_email_alert(self, to_email, subject, message):
        """Send email notification"""
        try:
            if not SMTP_USER or not SMTP_PASS:
                print("SMTP credentials not configured")
                return False
            
            msg = MimeMultipart()
            msg['From'] = SMTP_USER
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MimeText(message, 'plain'))
            
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            text = msg.as_string()
            server.sendmail(SMTP_USER, to_email, text)
            server.quit()
            
            print(f"Email sent to {to_email}")
            return True
        
        except Exception as e:
            print(f"Email sending error: {e}")
            return False
    
    def check_cooldown(self, well_id, alert_type):
        """Check if alert is in cooldown period"""
        key = f"{well_id}:{alert_type}"
        if key in self.alert_cooldown:
            last_sent = self.alert_cooldown[key]
            if datetime.now() - last_sent < timedelta(hours=1):  # 1 hour cooldown
                return True
        return False
    
    def set_cooldown(self, well_id, alert_type):
        """Set cooldown for alert type"""
        key = f"{well_id}:{alert_type}"
        self.alert_cooldown[key] = datetime.now()
    
    def process_water_level_alert(self, data):
        """Process water level related alerts"""
        try:
            well_id = data['well_id']
            water_level = data['water_level']
            
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Get well information and thresholds
            cur.execute("""
                SELECT w.*, u.email, u.full_name
                FROM wells w
                LEFT JOIN users u ON u.role = 'admin' OR u.username = 'admin'
                WHERE w.well_id = %s
            """, (well_id,))
            
            well_info = cur.fetchone()
            if not well_info:
                return
            
            alert_created = False
            
            # Check critical level
            if water_level <= well_info['critical_level']:
                if not self.check_cooldown(well_id, 'critical'):
                    # Create alert
                    cur.execute("""
                        INSERT INTO alerts (well_id, alert_type, severity, message, threshold_value, current_value)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        well_id,
                        'critical_water_level',
                        'critical',
                        f'CRITICAL: Water level at {well_info["name"]} is critically low at {water_level}m (threshold: {well_info["critical_level"]}m)',
                        well_info['critical_level'],
                        water_level
                    ))
                    
                    alert_id = cur.fetchone()['id']
                    alert_created = True
                    
                    # Send email notification
                    if well_info['email']:
                        subject = f"CRITICAL ALERT: {well_info['name']} Water Level"
                        message = f"""
                        CRITICAL WATER LEVEL ALERT
                        
                        Station: {well_info['name']} ({well_id})
                        Current Level: {water_level}m
                        Critical Threshold: {well_info['critical_level']}m
                        
                        Immediate action required!
                        
                        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                        """
                        
                        self.send_email_alert(well_info['email'], subject, message)
                    
                    self.set_cooldown(well_id, 'critical')
            
            # Check warning level
            elif water_level <= well_info['warning_level']:
                if not self.check_cooldown(well_id, 'warning'):
                    # Create alert
                    cur.execute("""
                        INSERT INTO alerts (well_id, alert_type, severity, message, threshold_value, current_value)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        well_id,
                        'low_water_level',
                        'warning',
                        f'WARNING: Water level at {well_info["name"]} is below warning threshold at {water_level}m (threshold: {well_info["warning_level"]}m)',
                        well_info['warning_level'],
                        water_level
                    ))
                    
                    alert_created = True
                    
                    # Send email notification
                    if well_info['email']:
                        subject = f"WARNING: {well_info['name']} Water Level"
                        message = f"""
                        WATER LEVEL WARNING
                        
                        Station: {well_info['name']} ({well_id})
                        Current Level: {water_level}m
                        Warning Threshold: {well_info['warning_level']}m
                        
                        Please monitor closely.
                        
                        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                        """
                        
                        self.send_email_alert(well_info['email'], subject, message)
                    
                    self.set_cooldown(well_id, 'warning')
            
            conn.commit()
            cur.close()
            conn.close()
            
            if alert_created:
                print(f"Alert created for well {well_id}")
        
        except Exception as e:
            print(f"Water level alert processing error: {e}")
    
    def process_battery_alert(self, data):
        """Process battery level alerts"""
        try:
            well_id = data['well_id']
            battery_level = data.get('battery_level')
            
            if battery_level is None or battery_level > 20:  # Only alert if below 20%
                return
            
            if self.check_cooldown(well_id, 'battery_low'):
                return
            
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Get well information
            cur.execute("""
                SELECT w.*, u.email
                FROM wells w
                LEFT JOIN users u ON u.role = 'admin'
                WHERE w.well_id = %s
                LIMIT 1
            """, (well_id,))
            
            well_info = cur.fetchone()
            if not well_info:
                return
            
            # Create battery alert
            cur.execute("""
                INSERT INTO alerts (well_id, alert_type, severity, message, threshold_value, current_value)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                well_id,
                'battery_low',
                'warning' if battery_level > 10 else 'critical',
                f'Battery level low at {well_info["name"]}: {battery_level}%',
                20.0,
                battery_level
            ))
            
            # Send email if configured
            if well_info['email']:
                subject = f"Battery Alert: {well_info['name']}"
                message = f"""
                BATTERY LEVEL ALERT
                
                Station: {well_info['name']} ({well_id})
                Battery Level: {battery_level}%
                
                Device may stop reporting soon. Please replace battery.
                
                Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """
                
                self.send_email_alert(well_info['email'], subject, message)
            
            conn.commit()
            cur.close()
            conn.close()
            
            self.set_cooldown(well_id, 'battery_low')
            print(f"Battery alert created for well {well_id}")
        
        except Exception as e:
            print(f"Battery alert processing error: {e}")
    
    def process_device_offline_alert(self, well_id):
        """Check for devices that haven't reported recently"""
        try:
            if self.check_cooldown(well_id, 'device_offline'):
                return
            
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Check last measurement time
            cur.execute("""
                SELECT w.*, m.time as last_reading, u.email
                FROM wells w
                LEFT JOIN LATERAL (
                    SELECT time FROM measurements_clean 
                    WHERE well_id = w.well_id 
                    ORDER BY time DESC LIMIT 1
                ) m ON true
                LEFT JOIN users u ON u.role = 'admin'
                WHERE w.well_id = %s
            """, (well_id,))
            
            well_info = cur.fetchone()
            if not well_info or not well_info['last_reading']:
                return
            
            # Check if device is offline (no data for 2+ hours)
            time_diff = datetime.now() - well_info['last_reading'].replace(tzinfo=None)
            if time_diff < timedelta(hours=2):
                return
            
            # Create offline alert
            cur.execute("""
                INSERT INTO alerts (well_id, alert_type, severity, message, threshold_value, current_value)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                well_id,
                'device_offline',
                'critical',
                f'Device at {well_info["name"]} appears offline. Last reading: {well_info["last_reading"]}',
                2.0,  # 2 hours threshold
                time_diff.total_seconds() / 3600  # Hours offline
            ))
            
            # Send email notification
            if well_info['email']:
                subject = f"Device Offline: {well_info['name']}"
                message = f"""
                DEVICE OFFLINE ALERT
                
                Station: {well_info['name']} ({well_id})
                Last Reading: {well_info['last_reading']}
                Offline Duration: {time_diff}
                
                Please check device connectivity and power.
                
                Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """
                
                self.send_email_alert(well_info['email'], subject, message)
            
            conn.commit()
            cur.close()
            conn.close()
            
            self.set_cooldown(well_id, 'device_offline')
            print(f"Device offline alert created for well {well_id}")
        
        except Exception as e:
            print(f"Device offline alert processing error: {e}")

def main():
    """Main alert processing loop"""
    print("Starting Alert Engine...")
    
    engine = AlertEngine()
    
    # Initialize Kafka consumer
    consumer = KafkaConsumer(
        'dwlr_readings',
        bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
        value_deserializer=lambda x: json.loads(x.decode('utf-8')),
        group_id='alert_engine'
    )
    
    print("Listening for measurements...")
    
    # Process incoming measurements
    for message in consumer:
        try:
            data = message.value
            
            # Process different types of alerts
            engine.process_water_level_alert(data)
            engine.process_battery_alert(data)
            
        except Exception as e:
            print(f"Message processing error: {e}")
            continue

if __name__ == "__main__":
    main()