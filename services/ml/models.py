from fastapi import FastAPI, HTTPException
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os
from datetime import datetime, timedelta
import redis
import json

app = FastAPI(title="Groundwater ML Service")

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/groundwater")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

redis_client = redis.from_url(REDIS_URL)

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

class WaterLevelPredictor:
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def prepare_features(self, df):
        """Prepare features for training/prediction"""
        # Time-based features
        df['hour'] = df['time'].dt.hour
        df['day_of_week'] = df['time'].dt.dayofweek
        df['month'] = df['time'].dt.month
        
        # Lag features
        df['water_level_lag1'] = df['water_level'].shift(1)
        df['water_level_lag24'] = df['water_level'].shift(24)
        
        # Rolling statistics
        df['water_level_ma7'] = df['water_level'].rolling(window=7).mean()
        df['water_level_std7'] = df['water_level'].rolling(window=7).std()
        
        # Temperature features if available
        if 'temperature' in df.columns:
            df['temp_ma3'] = df['temperature'].rolling(window=3).mean()
        
        return df
    
    def train(self, well_id):
        """Train model for specific well"""
        try:
            conn = get_db_connection()
            
            # Get training data
            query = """
                SELECT time, water_level, temperature, battery_level
                FROM measurements_clean
                WHERE well_id = %s
                AND time > NOW() - INTERVAL '30 days'
                ORDER BY time
            """
            
            df = pd.read_sql(query, conn, params=(well_id,))
            conn.close()
            
            if len(df) < 50:  # Need minimum data
                return False
            
            df['time'] = pd.to_datetime(df['time'])
            df = self.prepare_features(df)
            
            # Remove rows with NaN values
            df = df.dropna()
            
            if len(df) < 30:
                return False
            
            # Prepare features and target
            feature_cols = ['hour', 'day_of_week', 'month', 'water_level_lag1', 
                           'water_level_lag24', 'water_level_ma7', 'water_level_std7']
            
            if 'temp_ma3' in df.columns:
                feature_cols.append('temp_ma3')
            
            X = df[feature_cols].values
            y = df['water_level'].values
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.model.fit(X_scaled, y)
            self.is_trained = True
            
            # Save model
            model_path = f"/tmp/model_{well_id}.joblib"
            joblib.dump({
                'model': self.model,
                'scaler': self.scaler,
                'feature_cols': feature_cols
            }, model_path)
            
            return True
        
        except Exception as e:
            print(f"Training error: {e}")
            return False
    
    def predict(self, well_id, hours_ahead=24):
        """Generate predictions for next N hours"""
        try:
            # Load model if exists
            model_path = f"/tmp/model_{well_id}.joblib"
            if os.path.exists(model_path):
                saved_model = joblib.load(model_path)
                self.model = saved_model['model']
                self.scaler = saved_model['scaler']
                feature_cols = saved_model['feature_cols']
                self.is_trained = True
            
            if not self.is_trained:
                if not self.train(well_id):
                    return None
            
            conn = get_db_connection()
            
            # Get recent data for prediction
            query = """
                SELECT time, water_level, temperature, battery_level
                FROM measurements_clean
                WHERE well_id = %s
                ORDER BY time DESC
                LIMIT 100
            """
            
            df = pd.read_sql(query, conn, params=(well_id,))
            conn.close()
            
            if len(df) < 10:
                return None
            
            df = df.sort_values('time')
            df['time'] = pd.to_datetime(df['time'])
            df = self.prepare_features(df)
            
            predictions = []
            last_time = df['time'].iloc[-1]
            
            # Generate predictions for each hour
            for i in range(1, hours_ahead + 1):
                pred_time = last_time + timedelta(hours=i)
                
                # Create feature vector for prediction
                features = {
                    'hour': pred_time.hour,
                    'day_of_week': pred_time.dayofweek,
                    'month': pred_time.month,
                    'water_level_lag1': df['water_level'].iloc[-1],
                    'water_level_lag24': df['water_level'].iloc[-24] if len(df) >= 24 else df['water_level'].iloc[0],
                    'water_level_ma7': df['water_level'].tail(7).mean(),
                    'water_level_std7': df['water_level'].tail(7).std()
                }
                
                if 'temp_ma3' in feature_cols and 'temperature' in df.columns:
                    features['temp_ma3'] = df['temperature'].tail(3).mean()
                
                # Prepare feature vector
                X_pred = np.array([[features[col] for col in feature_cols]])
                X_pred_scaled = self.scaler.transform(X_pred)
                
                # Make prediction
                pred_level = self.model.predict(X_pred_scaled)[0]
                
                # Add confidence intervals (simple approach)
                confidence_range = 2.0  # ±2 meters
                
                predictions.append({
                    'forecast_time': pred_time.isoformat(),
                    'predicted_level': float(pred_level),
                    'confidence_lower': float(pred_level - confidence_range),
                    'confidence_upper': float(pred_level + confidence_range)
                })
            
            return predictions
        
        except Exception as e:
            print(f"Prediction error: {e}")
            return None

# Global predictor instance
predictor = WaterLevelPredictor()

@app.post("/train/{well_id}")
async def train_model(well_id: str):
    """Train ML model for specific well"""
    try:
        success = predictor.train(well_id)
        if success:
            return {"status": "success", "message": f"Model trained for well {well_id}"}
        else:
            raise HTTPException(status_code=400, detail="Insufficient data for training")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/predict/{well_id}")
async def predict_water_level(well_id: str, hours: int = 24):
    """Generate water level predictions"""
    try:
        # Check cache first
        cache_key = f"predictions:{well_id}:{hours}"
        cached_predictions = redis_client.get(cache_key)
        
        if cached_predictions:
            return json.loads(cached_predictions)
        
        predictions = predictor.predict(well_id, hours)
        
        if predictions is None:
            raise HTTPException(status_code=400, detail="Unable to generate predictions")
        
        # Cache predictions for 30 minutes
        redis_client.setex(cache_key, 1800, json.dumps(predictions))
        
        return predictions
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/retrain/all")
async def retrain_all_models():
    """Retrain models for all active wells"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT well_id FROM wells WHERE status = 'active'")
        wells = cur.fetchall()
        cur.close()
        conn.close()
        
        results = {}
        for well in wells:
            well_id = well['well_id']
            success = predictor.train(well_id)
            results[well_id] = "success" if success else "failed"
        
        return {"status": "completed", "results": results}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ml"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)