import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json
from datetime import datetime, timedelta
from kafka import KafkaConsumer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertEngine:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/groundwater")
        self.kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        
        # Email configuration
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        
        # Alert thresholds
        self.thresholds = {
            'critical_low_level': 20.0,  # meters
            'warning_low_level': 30.0,   # meters
            'high_rate_change': 5.0,     # meters per hour
            'device_offline_minutes': 60, # minutes
            'low_battery': 20.0          # percentage
        }
        
        # Kafka consumer for real-time alerts
        self.consumer = KafkaConsumer(
            'dwlr_readings',
            bootstrap_servers=[self.kafka_servers],
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            group_id='alert_engine'
        )
    
    def get_db_connection(self):
        return psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
    
    def check_water_level_alerts(self, well_id, current_level):
        """Check for water level threshold alerts"""
        alerts = []
        
        if current_level <= self.thresholds['critical_low_level']:
            alerts.append({
                'well_id': well_id,
                'alert_type': 'critical_low_level',
                'severity': 'critical',
                'message': f'Water level critically low: {current_level}m',
                'threshold_value': self.thresholds['critical_low_level'],
                'actual_value': current_level
            })
        elif current_level <= self.thresholds['warning_low_level']:
            alerts.append({
                'well_id': well_id,
                'alert_type': 'warning_low_level',
                'severity': 'warning',
                'message': f'Water level low: {current_level}m',
                'threshold_value': self.thresholds['warning_low_level'],
                'actual_value': current_level
            })
        
        return alerts
    
    def check_rate_change_alerts(self, well_id):
        """Check for rapid water level changes"""
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            # Get last 2 hours of data
            cur.execute("""
                SELECT water_level, time
                FROM measurements_clean
                WHERE well_id = %s 
                AND time > NOW() - INTERVAL '2 hours'
                ORDER BY time DESC
                LIMIT 10
            """, (well_id,))
            
            readings = cur.fetchall()
            cur.close()
            conn.close()
            
            if len(readings) < 2:
                return []
            
            # Calculate rate of change
            latest = readings[0]
            previous = readings[-1]
            
            time_diff = (latest['time'] - previous['time']).total_seconds() / 3600  # hours
            level_diff = abs(latest['water_level'] - previous['water_level'])
            
            if time_diff > 0:
                rate = level_diff / time_diff
                
                if rate > self.thresholds['high_rate_change']:
                    return [{
                        'well_id': well_id,
                        'alert_type': 'high_rate_change',
                        'severity': 'warning',
                        'message': f'Rapid water level change: {rate:.2f}m/h',
                        'threshold_value': self.thresholds['high_rate_change'],
                        'actual_value': rate
                    }]
            
            return []
            
        except Exception as e:
            logger.error(f"Rate change check error: {e}")
            return []
    
    def check_device_offline_alerts(self):
        """Check for offline devices"""
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            # Find wells with no recent data
            cur.execute("""
                SELECT w.well_id, w.name,
                       MAX(m.time) as last_reading
                FROM wells w
                LEFT JOIN measurements_clean m ON w.well_id = m.well_id
                WHERE w.status = 'active'
                GROUP BY w.well_id, w.name
                HAVING MAX(m.time) < NOW() - INTERVAL '%s minutes'
                   OR MAX(m.time) IS NULL
            """, (self.thresholds['device_offline_minutes'],))
            
            offline_wells = cur.fetchall()
            cur.close()
            conn.close()
            
            alerts = []
            for well in offline_wells:
                alerts.append({
                    'well_id': well['well_id'],
                    'alert_type': 'device_offline',
                    'severity': 'warning',
                    'message': f'Device offline for {self.thresholds["device_offline_minutes"]} minutes',
                    'threshold_value': self.thresholds['device_offline_minutes'],
                    'actual_value': None
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Device offline check error: {e}")
            return []
    
    def check_battery_alerts(self, well_id, battery_level):
        """Check for low battery alerts"""
        if battery_level and battery_level <= self.thresholds['low_battery']:
            return [{
                'well_id': well_id,
                'alert_type': 'low_battery',
                'severity': 'warning',
                'message': f'Low battery: {battery_level}%',
                'threshold_value': self.thresholds['low_battery'],
                'actual_value': battery_level
            }]
        return []
    
    def create_alert(self, alert_data):
        """Create alert in database"""
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            # Check if similar alert already exists and is active
            cur.execute("""
                SELECT id FROM alerts
                WHERE well_id = %s 
                AND alert_type = %s 
                AND is_active = true
                AND created_at > NOW() - INTERVAL '1 hour'
            """, (alert_data['well_id'], alert_data['alert_type']))
            
            if cur.fetchone():
                cur.close()
                conn.close()
                return None  # Don't create duplicate alert
            
            # Create new alert
            cur.execute("""
                INSERT INTO alerts 
                (well_id, alert_type, severity, message, threshold_value, actual_value)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                alert_data['well_id'],
                alert_data['alert_type'],
                alert_data['severity'],
                alert_data['message'],
                alert_data.get('threshold_value'),
                alert_data.get('actual_value')
            ))
            
            alert_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"Created alert {alert_id} for well {alert_data['well_id']}")
            return alert_id
            
        except Exception as e:
            logger.error(f"Alert creation error: {e}")
            return None
    
    def send_email_alert(self, alert_data):
        """Send email notification for alert"""
        if not self.smtp_user or not self.smtp_password:
            logger.warning("Email credentials not configured")
            return False
        
        try:
            # Get recipient emails
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT email FROM users 
                WHERE role IN ('admin', 'manager') 
                AND is_active = true
            """)
            
            recipients = [row[0] for row in cur.fetchall()]
            cur.close()
            conn.close()
            
            if not recipients:
                logger.warning("No email recipients found")
                return False
            
            # Create email
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"Groundwater Alert: {alert_data['alert_type']} - {alert_data['well_id']}"
            
            body = f"""
            Alert Details:
            
            Well ID: {alert_data['well_id']}
            Alert Type: {alert_data['alert_type']}
            Severity: {alert_data['severity']}
            Message: {alert_data['message']}
            
            Threshold: {alert_data.get('threshold_value', 'N/A')}
            Actual Value: {alert_data.get('actual_value', 'N/A')}
            
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            Please check the dashboard for more details.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email alert sent for {alert_data['well_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Email sending error: {e}")
            return False
    
    def process_real_time_data(self, data):
        """Process incoming data for real-time alerts"""
        well_id = data['well_id']
        water_level = data.get('water_level')
        battery_level = data.get('battery_level')
        
        all_alerts = []
        
        # Check water level alerts
        if water_level:
            all_alerts.extend(self.check_water_level_alerts(well_id, water_level))
        
        # Check battery alerts
        if battery_level:
            all_alerts.extend(self.check_battery_alerts(well_id, battery_level))
        
        # Check rate change alerts
        all_alerts.extend(self.check_rate_change_alerts(well_id))
        
        # Create and send alerts
        for alert_data in all_alerts:
            alert_id = self.create_alert(alert_data)
            if alert_id and alert_data['severity'] in ['critical', 'warning']:
                self.send_email_alert(alert_data)
    
    def run_periodic_checks(self):
        """Run periodic alert checks"""
        logger.info("Running periodic alert checks...")
        
        # Check for offline devices
        offline_alerts = self.check_device_offline_alerts()
        
        for alert_data in offline_alerts:
            alert_id = self.create_alert(alert_data)
            if alert_id:
                self.send_email_alert(alert_data)
    
    def run_real_time_processor(self):
        """Run real-time alert processor"""
        logger.info("Starting real-time alert processor...")
        
        try:
            for message in self.consumer:
                data = message.value
                self.process_real_time_data(data)
                
        except KeyboardInterrupt:
            logger.info("Stopping alert processor...")
        except Exception as e:
            logger.error(f"Alert processor error: {e}")
        finally:
            self.consumer.close()

if __name__ == "__main__":
    engine = AlertEngine()
    
    # Run periodic checks first
    engine.run_periodic_checks()
    
    # Start real-time processing
    engine.run_real_time_processor()