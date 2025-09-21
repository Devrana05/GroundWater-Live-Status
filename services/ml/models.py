import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from prophet import Prophet
import joblib
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def prepare_features(self, df):
        """Prepare features for anomaly detection"""
        features = []
        
        if 'water_level' in df.columns:
            features.append('water_level')
        
        if 'battery_level' in df.columns:
            features.append('battery_level')
        
        # Add time-based features
        df['hour'] = df['time'].dt.hour
        df['day_of_week'] = df['time'].dt.dayofweek
        features.extend(['hour', 'day_of_week'])
        
        # Add rolling statistics
        if len(df) > 24:  # Need enough data for rolling window
            df['water_level_rolling_mean'] = df['water_level'].rolling(window=24).mean()
            df['water_level_rolling_std'] = df['water_level'].rolling(window=24).std()
            features.extend(['water_level_rolling_mean', 'water_level_rolling_std'])
        
        return df[features].fillna(method='ffill').fillna(0)
    
    def train(self, df):
        """Train anomaly detection model"""
        try:
            features = self.prepare_features(df)
            
            if len(features) < 100:  # Need minimum data for training
                logger.warning("Insufficient data for training anomaly detector")
                return False
            
            # Scale features
            features_scaled = self.scaler.fit_transform(features)
            
            # Train model
            self.model.fit(features_scaled)
            self.is_trained = True
            
            logger.info(f"Anomaly detector trained on {len(features)} samples")
            return True
            
        except Exception as e:
            logger.error(f"Anomaly detector training error: {e}")
            return False
    
    def predict(self, df):
        """Predict anomalies in data"""
        if not self.is_trained:
            logger.warning("Model not trained yet")
            return np.array([])
        
        try:
            features = self.prepare_features(df)
            features_scaled = self.scaler.transform(features)
            
            # Predict (-1 for anomaly, 1 for normal)
            predictions = self.model.predict(features_scaled)
            anomaly_scores = self.model.decision_function(features_scaled)
            
            return predictions, anomaly_scores
            
        except Exception as e:
            logger.error(f"Anomaly prediction error: {e}")
            return np.array([]), np.array([])

class WaterLevelForecaster:
    def __init__(self):
        self.model = None
        self.is_trained = False
    
    def prepare_data(self, df):
        """Prepare data for Prophet forecasting"""
        # Prophet requires 'ds' (datestamp) and 'y' (value) columns
        forecast_df = df[['time', 'water_level']].copy()
        forecast_df.columns = ['ds', 'y']
        
        # Remove outliers for better forecasting
        Q1 = forecast_df['y'].quantile(0.25)
        Q3 = forecast_df['y'].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        forecast_df = forecast_df[
            (forecast_df['y'] >= lower_bound) & 
            (forecast_df['y'] <= upper_bound)
        ]
        
        return forecast_df
    
    def train(self, df):
        """Train forecasting model"""
        try:
            if len(df) < 100:  # Need minimum data for forecasting
                logger.warning("Insufficient data for training forecaster")
                return False
            
            forecast_df = self.prepare_data(df)
            
            # Initialize Prophet model
            self.model = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=False,
                changepoint_prior_scale=0.05,
                seasonality_prior_scale=10.0
            )
            
            # Fit model
            self.model.fit(forecast_df)
            self.is_trained = True
            
            logger.info(f"Forecaster trained on {len(forecast_df)} samples")
            return True
            
        except Exception as e:
            logger.error(f"Forecaster training error: {e}")
            return False
    
    def forecast(self, periods=168):  # 7 days * 24 hours
        """Generate forecast for specified periods (hours)"""
        if not self.is_trained:
            logger.warning("Forecaster not trained yet")
            return pd.DataFrame()
        
        try:
            # Create future dataframe
            future = self.model.make_future_dataframe(periods=periods, freq='H')
            
            # Generate forecast
            forecast = self.model.predict(future)
            
            # Return only future predictions
            forecast_future = forecast.tail(periods)[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
            forecast_future.columns = ['forecast_time', 'predicted_level', 'confidence_lower', 'confidence_upper']
            
            return forecast_future
            
        except Exception as e:
            logger.error(f"Forecasting error: {e}")
            return pd.DataFrame()

class MLModelManager:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/groundwater")
        self.models = {}
    
    def get_db_connection(self):
        return psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
    
    def load_well_data(self, well_id, days=30):
        """Load training data for a specific well"""
        try:
            conn = self.get_db_connection()
            
            query = """
                SELECT time, water_level, battery_level, temperature
                FROM measurements_clean
                WHERE well_id = %s 
                AND time > NOW() - INTERVAL '%s days'
                AND quality_flag = 'good'
                ORDER BY time
            """
            
            df = pd.read_sql(query, conn, params=(well_id, days))
            conn.close()
            
            if not df.empty:
                df['time'] = pd.to_datetime(df['time'])
            
            return df
            
        except Exception as e:
            logger.error(f"Data loading error: {e}")
            return pd.DataFrame()
    
    def train_models_for_well(self, well_id):
        """Train both anomaly detection and forecasting models for a well"""
        logger.info(f"Training models for well {well_id}")
        
        # Load data
        df = self.load_well_data(well_id, days=90)  # 3 months of data
        
        if df.empty or len(df) < 100:
            logger.warning(f"Insufficient data for well {well_id}")
            return False
        
        # Train anomaly detector
        anomaly_detector = AnomalyDetector()
        anomaly_trained = anomaly_detector.train(df)
        
        # Train forecaster
        forecaster = WaterLevelForecaster()
        forecast_trained = forecaster.train(df)
        
        if anomaly_trained or forecast_trained:
            self.models[well_id] = {
                'anomaly_detector': anomaly_detector if anomaly_trained else None,
                'forecaster': forecaster if forecast_trained else None,
                'last_trained': datetime.now()
            }
            
            # Save models to database
            self.save_models_to_db(well_id)
            
            return True
        
        return False
    
    def save_models_to_db(self, well_id):
        """Save trained models to database"""
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            models = self.models.get(well_id, {})
            
            # Save anomaly detector
            if models.get('anomaly_detector'):
                model_data = joblib.dumps(models['anomaly_detector'])
                
                cur.execute("""
                    INSERT INTO ml_models (model_name, model_type, well_id, model_data, version)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (model_name, well_id) DO UPDATE SET
                        model_data = EXCLUDED.model_data,
                        version = EXCLUDED.version,
                        created_at = NOW()
                """, (f"anomaly_detector_{well_id}", "anomaly_detection", well_id, model_data, "1.0"))
            
            # Save forecaster
            if models.get('forecaster'):
                model_data = joblib.dumps(models['forecaster'])
                
                cur.execute("""
                    INSERT INTO ml_models (model_name, model_type, well_id, model_data, version)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (model_name, well_id) DO UPDATE SET
                        model_data = EXCLUDED.model_data,
                        version = EXCLUDED.version,
                        created_at = NOW()
                """, (f"forecaster_{well_id}", "forecasting", well_id, model_data, "1.0"))
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"Models saved for well {well_id}")
            
        except Exception as e:
            logger.error(f"Model saving error: {e}")
    
    def generate_forecasts_for_well(self, well_id):
        """Generate and store forecasts for a well"""
        try:
            models = self.models.get(well_id, {})
            forecaster = models.get('forecaster')
            
            if not forecaster:
                logger.warning(f"No forecaster available for well {well_id}")
                return False
            
            # Generate 7-day forecast
            forecast_df = forecaster.forecast(periods=168)
            
            if forecast_df.empty:
                return False
            
            # Store forecasts in database
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            # Clear old forecasts
            cur.execute("DELETE FROM forecasts WHERE well_id = %s", (well_id,))
            
            # Insert new forecasts
            for _, row in forecast_df.iterrows():
                cur.execute("""
                    INSERT INTO forecasts 
                    (well_id, forecast_time, predicted_level, confidence_lower, confidence_upper)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    well_id,
                    row['forecast_time'],
                    row['predicted_level'],
                    row['confidence_lower'],
                    row['confidence_upper']
                ))
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"Generated {len(forecast_df)} forecasts for well {well_id}")
            return True
            
        except Exception as e:
            logger.error(f"Forecast generation error: {e}")
            return False
    
    def train_all_models(self):
        """Train models for all active wells"""
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            cur.execute("SELECT well_id FROM wells WHERE status = 'active'")
            wells = [row[0] for row in cur.fetchall()]
            
            cur.close()
            conn.close()
            
            for well_id in wells:
                success = self.train_models_for_well(well_id)
                if success:
                    self.generate_forecasts_for_well(well_id)
            
            logger.info(f"Training completed for {len(wells)} wells")
            
        except Exception as e:
            logger.error(f"Batch training error: {e}")

if __name__ == "__main__":
    manager = MLModelManager()
    manager.train_all_models()