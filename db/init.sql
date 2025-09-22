-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Wells/Stations table
CREATE TABLE IF NOT EXISTS wells (
    well_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    depth DECIMAL(8, 2),
    critical_level DECIMAL(8, 2),
    warning_level DECIMAL(8, 2),
    status VARCHAR(20) DEFAULT 'active',
    installation_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Raw measurements table
CREATE TABLE IF NOT EXISTS measurements_raw (
    id BIGSERIAL,
    time TIMESTAMPTZ NOT NULL,
    well_id VARCHAR(50) NOT NULL,
    water_level DECIMAL(8, 2),
    battery_level DECIMAL(5, 2),
    temperature DECIMAL(5, 2),
    device_status VARCHAR(20),
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (id, time)
);

-- Clean measurements table (after ETL processing)
CREATE TABLE IF NOT EXISTS measurements_clean (
    id BIGSERIAL,
    time TIMESTAMPTZ NOT NULL,
    well_id VARCHAR(50) NOT NULL,
    water_level DECIMAL(8, 2),
    battery_level DECIMAL(5, 2),
    temperature DECIMAL(5, 2),
    device_status VARCHAR(20),
    quality_score DECIMAL(3, 2),
    PRIMARY KEY (id, time),
    FOREIGN KEY (well_id) REFERENCES wells(well_id)
);

-- Alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    well_id VARCHAR(50) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT,
    threshold_value DECIMAL(8, 2),
    current_value DECIMAL(8, 2),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    FOREIGN KEY (well_id) REFERENCES wells(well_id)
);

-- Forecasts table
CREATE TABLE IF NOT EXISTS forecasts (
    id SERIAL PRIMARY KEY,
    well_id VARCHAR(50) NOT NULL,
    forecast_time TIMESTAMPTZ NOT NULL,
    predicted_level DECIMAL(8, 2),
    confidence_lower DECIMAL(8, 2),
    confidence_upper DECIMAL(8, 2),
    model_version VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (well_id) REFERENCES wells(well_id)
);

-- Convert tables to hypertables for time-series optimization
SELECT create_hypertable('measurements_raw', 'time', if_not_exists => TRUE);
SELECT create_hypertable('measurements_clean', 'time', if_not_exists => TRUE);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_measurements_raw_well_time ON measurements_raw (well_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_measurements_clean_well_time ON measurements_clean (well_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_well_active ON alerts (well_id, is_active);
CREATE INDEX IF NOT EXISTS idx_forecasts_well_time ON forecasts (well_id, forecast_time);

-- Insert default admin user (password: admin123)
INSERT INTO users (username, email, password_hash, full_name, role) 
VALUES ('admin', 'admin@groundwater.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3QJflLxQjO', 'System Administrator', 'admin')
ON CONFLICT (username) DO NOTHING;

-- Insert sample wells
INSERT INTO wells (well_id, name, latitude, longitude, depth, critical_level, warning_level) VALUES
('ST001', 'Station Alpha', 28.6139, 77.2090, 50.0, 10.0, 15.0),
('ST002', 'Station Beta', 28.7041, 77.1025, 45.0, 8.0, 12.0),
('ST003', 'Station Gamma', 28.5355, 77.3910, 60.0, 12.0, 18.0),
('ST004', 'Station Delta', 28.4595, 77.0266, 55.0, 9.0, 14.0),
('ST005', 'Station Echo', 28.6692, 77.4538, 48.0, 11.0, 16.0)
ON CONFLICT (well_id) DO NOTHING;

-- Insert sample measurements
INSERT INTO measurements_clean (time, well_id, water_level, battery_level, temperature, device_status, quality_score) VALUES
(NOW() - INTERVAL '1 hour', 'ST001', 25.5, 85.2, 22.1, 'online', 0.95),
(NOW() - INTERVAL '2 hours', 'ST001', 25.3, 84.8, 22.3, 'online', 0.94),
(NOW() - INTERVAL '1 hour', 'ST002', 18.7, 78.5, 21.8, 'online', 0.96),
(NOW() - INTERVAL '2 hours', 'ST002', 18.9, 78.1, 21.6, 'online', 0.95),
(NOW() - INTERVAL '1 hour', 'ST003', 32.1, 92.3, 23.2, 'online', 0.97),
(NOW() - INTERVAL '2 hours', 'ST003', 31.8, 91.9, 23.0, 'online', 0.96)
ON CONFLICT DO NOTHING;

-- Insert sample alerts
INSERT INTO alerts (well_id, alert_type, severity, message, threshold_value, current_value) VALUES
('ST002', 'low_water_level', 'warning', 'Water level approaching warning threshold', 12.0, 18.7),
('ST001', 'battery_low', 'info', 'Battery level below 90%', 90.0, 85.2)
ON CONFLICT DO NOTHING;