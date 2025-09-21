-- Enable TimescaleDB and PostGIS extensions
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS postgis;

-- Wells table
CREATE TABLE wells (
    id SERIAL PRIMARY KEY,
    well_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100),
    location GEOMETRY(POINT, 4326),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    depth_total DECIMAL(8, 2),
    installation_date DATE,
    status VARCHAR(20) DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Raw measurements table (hypertable)
CREATE TABLE measurements_raw (
    time TIMESTAMPTZ NOT NULL,
    well_id VARCHAR(50) NOT NULL,
    water_level DECIMAL(8, 2),
    battery_level DECIMAL(5, 2),
    temperature DECIMAL(5, 2),
    quality_flag VARCHAR(10) DEFAULT 'good',
    device_status VARCHAR(20) DEFAULT 'online',
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Convert to hypertable
SELECT create_hypertable('measurements_raw', 'time');

-- Cleaned measurements table (hypertable)
CREATE TABLE measurements_clean (
    time TIMESTAMPTZ NOT NULL,
    well_id VARCHAR(50) NOT NULL,
    water_level DECIMAL(8, 2),
    battery_level DECIMAL(5, 2),
    temperature DECIMAL(5, 2),
    quality_flag VARCHAR(10) DEFAULT 'good',
    is_interpolated BOOLEAN DEFAULT FALSE,
    processing_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

SELECT create_hypertable('measurements_clean', 'time');

-- Alerts table
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    well_id VARCHAR(50) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT,
    threshold_value DECIMAL(8, 2),
    actual_value DECIMAL(8, 2),
    is_active BOOLEAN DEFAULT TRUE,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- ML Models table
CREATE TABLE ml_models (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    well_id VARCHAR(50),
    model_data BYTEA,
    metrics JSONB,
    version VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Forecasts table
CREATE TABLE forecasts (
    id SERIAL PRIMARY KEY,
    well_id VARCHAR(50) NOT NULL,
    forecast_time TIMESTAMPTZ NOT NULL,
    predicted_level DECIMAL(8, 2),
    confidence_lower DECIMAL(8, 2),
    confidence_upper DECIMAL(8, 2),
    model_id INTEGER REFERENCES ml_models(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_measurements_raw_well_time ON measurements_raw (well_id, time DESC);
CREATE INDEX idx_measurements_clean_well_time ON measurements_clean (well_id, time DESC);
CREATE INDEX idx_alerts_well_active ON alerts (well_id, is_active);
CREATE INDEX idx_forecasts_well_time ON forecasts (well_id, forecast_time);
CREATE INDEX idx_wells_location ON wells USING GIST (location);

-- Sample data
INSERT INTO wells (well_id, name, latitude, longitude, depth_total) VALUES
('ST001', 'Station 001', 28.6139, 77.2090, 50.0),
('ST002', 'Station 002', 28.6289, 77.2194, 60.0),
('ST003', 'Station 003', 28.6089, 77.1986, 45.0);

UPDATE wells SET location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326);

-- Sample measurements
INSERT INTO measurements_raw (time, well_id, water_level, battery_level, temperature) VALUES
(NOW() - INTERVAL '1 hour', 'ST001', 18.5, 85.2, 22.1),
(NOW() - INTERVAL '2 hours', 'ST001', 18.7, 85.0, 22.3),
(NOW() - INTERVAL '1 hour', 'ST002', 42.1, 92.1, 21.8),
(NOW() - INTERVAL '2 hours', 'ST002', 42.3, 92.0, 21.9);

-- Copy to clean table
INSERT INTO measurements_clean (time, well_id, water_level, battery_level, temperature)
SELECT time, well_id, water_level, battery_level, temperature FROM measurements_raw;

-- Sample alerts
INSERT INTO alerts (well_id, alert_type, severity, message, threshold_value, actual_value) VALUES
('ST001', 'low_water_level', 'critical', 'Water level below critical threshold', 20.0, 18.5),
('ST003', 'device_offline', 'warning', 'No data received for 30 minutes', NULL, NULL);

-- Default user
INSERT INTO users (username, email, password_hash, role) VALUES
('admin', 'admin@groundwater.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.Gm.F5u', 'admin');