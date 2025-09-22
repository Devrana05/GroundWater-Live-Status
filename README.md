# Groundwater Real-Time Monitoring System

A complete end-to-end solution for real-time groundwater resource evaluation using Digital Water Level Recorder (DWLR) data.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose (Recommended)
- Web Browser (Chrome, Firefox, Safari)
- Python 3.8+ (for development)

### 1. Clone Repository
```bash
git clone <repository-url>
cd SIH
```

### 2. Full Stack Deployment (Recommended)
```bash
# Windows
start.bat

# Linux/Mac
chmod +x start.sh
./start.sh
```

### 3. Frontend Only (Development)
```bash
# Open HTML files directly in browser
open index.html
# Or serve with Python
python -m http.server 8080
```

### 4. Manual Backend Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Start individual services
cd services/api && python main.py
cd services/ingest && python main.py
cd services/etl && python processor.py
cd services/ml && python models.py
cd services/alerts && python engine.py
```

## 📊 Features

### Frontend Dashboard
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Dark/Light Theme** - Dynamic theme switching with persistence
- **Interactive Maps** - Station locations with status indicators using Leaflet.js
- **Real-time Charts** - Water level trends using Chart.js
- **Alert Management** - Cross-page notification system
- **Data Filtering** - Station and status-based filtering
- **Mobile Navigation** - Collapsible sidebar for mobile devices

### Data Explorer
- **Station Selector** - Filter data by specific monitoring stations
- **Status Filter** - Filter by critical, warning, or normal status
- **Responsive Tables** - Dynamic data updates based on selections
- **Overview Cards** - Real-time count updates for different alert types
- **No Data Handling** - Clear messaging when no data matches filters

### Backend Services (Python)
- **Data Ingestion** - FastAPI service for DWLR data collection
- **MQTT Support** - Real-time device communication
- **Database Integration** - PostgreSQL/TimescaleDB support
- **Message Queue** - Kafka integration for data streaming

## 📁 Project Structure

```
SIH/
├── services/
│   ├── ingest/          # Data ingestion service (Python/FastAPI)
│   │   ├── main.py      # FastAPI ingest service
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── api/             # REST API service (Python/FastAPI)
│   │   └── main.py
│   ├── etl/             # ETL processing (Python)
│   │   └── processor.py
│   ├── ml/              # ML models & training (Python)
│   │   └── models.py
│   └── alerts/          # Alert engine (Python)
│       └── engine.py
├── db/
│   └── init.sql         # Database schema
├── monitoring/
│   └── prometheus.yml   # Prometheus configuration
├── mqtt/
│   └── mosquitto.conf   # MQTT broker configuration
├── index.html           # Main dashboard page
├── alerts.html          # Alerts management page
├── stations.html        # Stations monitoring page
├── data-explorer.html   # Data exploration page
├── styles.css           # Main stylesheet with theme support
├── script.js            # Dashboard JavaScript
├── alerts.js            # Alerts page JavaScript with filtering
├── stations.js          # Stations page JavaScript
├── data-explorer.js     # Data explorer with responsive filtering
├── shared-notifications.js # Cross-page notification system
├── theme-init.js        # Instant theme initialization
├── test_data_generator.py # Test data generation script
├── requirements.txt     # Python dependencies
├── docker-compose.yml   # Docker services configuration
└── README.md
```

## 🛠️ Technologies Used

### Frontend
- **HTML5** - Page structure and markup
- **CSS3** - Styling, responsive design, dark/light themes
- **JavaScript (ES6)** - Interactive functionality and data filtering
- **Leaflet.js** - Interactive maps for station locations
- **Chart.js** - Data visualization and trend charts
- **Font Awesome** - Icon library

### Backend
- **Python 3.8+** - Backend services
- **FastAPI** - REST API framework
- **Pydantic** - Data validation
- **Asyncio** - Asynchronous programming
- **psycopg2** - PostgreSQL database adapter
- **paho-mqtt** - MQTT client library
- **kafka-python** - Kafka message streaming

### Database & Messaging
- **TimescaleDB/PostgreSQL** - Time-series data storage
- **Apache Kafka** - Message streaming
- **MQTT (Mosquitto)** - IoT device communication

## 🎯 Pages

1. **Dashboard** (`index.html`) - Overview with maps and charts
2. **Data Explorer** (`data-explorer.html`) - Filterable data tables with station/status selectors
3. **Alerts** (`alerts.html`) - Alert management with filtering and cross-page notifications
4. **Stations** (`stations.html`) - Station monitoring with real-time status updates

## 📚 API Endpoints

### Data Ingestion
- `POST /ingest/dwlr` - Submit DWLR reading
- `GET /health` - Service health check

### Testing Data Ingestion
```bash
# HTTP Test
curl -X POST "http://localhost:8000/ingest/dwlr" \
  -H "Content-Type: application/json" \
  -d '{
    "well_id": "ST001",
    "timestamp": "2024-01-15T14:30:00Z",
    "water_level": 25.5,
    "battery_level": 85.2,
    "temperature": 22.1
  }'

# Generate test data
python test_data_generator.py
```

## 🎯 Current Implementation

### ✅ Completed Features
- **Responsive Dashboard** - Works on all device sizes
- **Dark/Light Theme** - Instant theme switching with localStorage persistence
- **Interactive Maps** - Station locations with color-coded status indicators
- **Data Filtering** - Station and status-based filtering in data explorer
- **Alert Management** - Cross-page notification system with filtering
- **Data Ingestion API** - FastAPI backend for DWLR data collection
- **MQTT Integration** - Real-time device communication support

### 🔄 Backend Services Available
- **Ingest Service** - FastAPI service for data collection
- **Database Schema** - PostgreSQL/TimescaleDB structure
- **Docker Configuration** - Multi-service orchestration
- **MQTT Broker** - Device communication setup

## 🚀 Getting Started

### Option 1: Full Stack (Recommended)
```bash
# Windows
start.bat

# Linux/Mac
chmod +x start.sh && ./start.sh
```

### Option 2: Docker Compose
```bash
docker-compose up -d --build
```

### Option 3: Frontend Only
```bash
# Open index.html in browser or
python -m http.server 8080
```

### Option 4: Development Mode
```bash
# Start individual services
cd services/api && python main.py
cd services/ingest && python main.py
# etc...
```

## 🌐 Access Points

- **Web Dashboard**: http://localhost
- **Mobile Interface**: http://mobile.localhost
- **API Documentation**: http://localhost/api/docs
- **Mobile API Docs**: http://mobile.localhost/api/docs
- **Grafana Monitoring**: http://localhost:3002 (admin/admin)
- **Prometheus Metrics**: http://localhost:9090

## 👤 Default Login
- **Username**: admin
- **Password**: admin123

## 📄 License

This project is licensed under the MIT License.