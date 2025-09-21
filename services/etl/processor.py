import pandas as pd
import numpy as np
from kafka import KafkaConsumer
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os
from datetime import datetime, timedelta
from scipy import interpolate
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ETLProcessor:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/groundwater")
        self.kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        
        # Kafka consumer
        self.consumer = KafkaConsumer(
            'dwlr_readings',
            bootstrap_servers=[self.kafka_servers],
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            group_id='etl_processor'
        )
    
    def get_db_connection(self):
        return psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
    
    def remove_outliers(self, df, column='water_level', method='iqr', threshold=1.5):
        """Remove outliers using IQR method"""
        if df.empty or column not in df.columns:
            return df
        
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - threshold * IQR
        upper_bound = Q3 + threshold * IQR
        
        # Mark outliers but don't remove them completely
        df['is_outlier'] = (df[column] < lower_bound) | (df[column] > upper_bound)
        
        return df
    
    def interpolate_gaps(self, df, column='water_level', max_gap_hours=6):
        """Interpolate short gaps in data"""
        if df.empty or column not in df.columns:
            return df
        
        df = df.sort_values('time')
        df['time_diff'] = df['time'].diff().dt.total_seconds() / 3600  # hours
        
        # Only interpolate gaps smaller than max_gap_hours
        mask = (df['time_diff'] <= max_gap_hours) & (df[column].isna())
        
        if mask.any():
            # Linear interpolation
            df.loc[mask, column] = df[column].interpolate(method='linear')
            df.loc[mask, 'is_interpolated'] = True
            df.loc[mask, 'processing_notes'] = f'Interpolated gap <= {max_gap_hours}h'
        
        return df
    
    def normalize_timestamps(self, df):
        """Normalize timestamps to consistent intervals"""
        if df.empty:
            return df
        
        # Round timestamps to nearest 15 minutes
        df['time'] = df['time'].dt.round('15min')
        
        # Remove duplicates, keeping the first occurrence
        df = df.drop_duplicates(subset=['well_id', 'time'], keep='first')
        
        return df
    
    def validate_data(self, data):
        """Validate incoming data"""
        required_fields = ['well_id', 'timestamp', 'water_level']
        
        for field in required_fields:
            if field not in data:
                return False, f"Missing required field: {field}"
        
        # Check data types and ranges
        try:
            water_level = float(data['water_level'])
            if water_level < 0 or water_level > 200:  # Reasonable range
                return False, "Water level out of reasonable range"
        except (ValueError, TypeError):
            return False, "Invalid water level value"
        
        return True, "Valid"
    
    def process_batch_data(self, well_id, start_time, end_time):
        """Process historical data in batches"""
        try:
            conn = self.get_db_connection()
            
            # Fetch raw data
            query = """
                SELECT * FROM measurements_raw
                WHERE well_id = %s 
                AND time BETWEEN %s AND %s
                ORDER BY time
            """
            
            df = pd.read_sql(query, conn, params=(well_id, start_time, end_time))
            
            if df.empty:
                logger.info(f"No data found for well {well_id}")
                return
            
            # Convert timestamp column
            df['time'] = pd.to_datetime(df['time'])
            
            # Data cleaning pipeline
            df = self.normalize_timestamps(df)
            df = self.remove_outliers(df)
            df = self.interpolate_gaps(df)
            
            # Add processing metadata
            df['is_interpolated'] = df.get('is_interpolated', False)
            df['processing_notes'] = df.get('processing_notes', 'Batch processed')
            
            # Insert cleaned data
            cur = conn.cursor()
            
            for _, row in df.iterrows():
                cur.execute("""
                    INSERT INTO measurements_clean 
                    (time, well_id, water_level, battery_level, temperature, 
                     quality_flag, is_interpolated, processing_notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (well_id, time) DO UPDATE SET
                        water_level = EXCLUDED.water_level,
                        processing_notes = EXCLUDED.processing_notes
                """, (
                    row['time'],
                    row['well_id'],
                    row['water_level'],
                    row.get('battery_level'),
                    row.get('temperature'),
                    'poor' if row.get('is_outlier', False) else 'good',
                    row.get('is_interpolated', False),
                    row.get('processing_notes', '')
                ))
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"Processed {len(df)} records for well {well_id}")
            
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
    
    def process_stream_data(self, data):
        """Process real-time streaming data"""
        try:
            # Validate data
            is_valid, message = self.validate_data(data)
            if not is_valid:
                logger.warning(f"Invalid data: {message}")
                return
            
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            # Simple real-time processing
            timestamp = pd.to_datetime(data['timestamp'])
            
            # Check for duplicates
            cur.execute("""
                SELECT COUNT(*) FROM measurements_clean
                WHERE well_id = %s AND time = %s
            """, (data['well_id'], timestamp))
            
            if cur.fetchone()[0] > 0:
                logger.info(f"Duplicate data for {data['well_id']} at {timestamp}")
                cur.close()
                conn.close()
                return
            
            # Insert cleaned data
            cur.execute("""
                INSERT INTO measurements_clean 
                (time, well_id, water_level, battery_level, temperature, quality_flag)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                timestamp,
                data['well_id'],
                data['water_level'],
                data.get('battery_level'),
                data.get('temperature'),
                'good'
            ))
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"Processed real-time data for {data['well_id']}")
            
        except Exception as e:
            logger.error(f"Stream processing error: {e}")
    
    def run_stream_processor(self):
        """Run the streaming ETL processor"""
        logger.info("Starting stream processor...")
        
        try:
            for message in self.consumer:
                data = message.value
                self.process_stream_data(data)
                
        except KeyboardInterrupt:
            logger.info("Stopping stream processor...")
        except Exception as e:
            logger.error(f"Stream processor error: {e}")
        finally:
            self.consumer.close()
    
    def run_batch_processor(self):
        """Run batch processing for historical data"""
        logger.info("Starting batch processor...")
        
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            # Get all wells
            cur.execute("SELECT well_id FROM wells WHERE status = 'active'")
            wells = [row[0] for row in cur.fetchall()]
            
            # Process last 24 hours for each well
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            
            for well_id in wells:
                self.process_batch_data(well_id, start_time, end_time)
            
            cur.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Batch processor error: {e}")

if __name__ == "__main__":
    processor = ETLProcessor()
    
    # Run batch processing first
    processor.run_batch_processor()
    
    # Then start stream processing
    processor.run_stream_processor()