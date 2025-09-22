# Groundwater Real-Time Monitoring System

A complete end-to-end solution for real-time groundwater resource evaluation using Digital Water Level Recorder (DWLR) data.

## 🚀 Quick Start

### Prerequisites
- Web Browser (Chrome, Firefox, Safari)
- Python 3.8+ (for backend services)

### 1. Clone Repository
```bash
git clone https://github.com/Devrana05/GroundWater-Live-Status SIH
cd SIH
```

### 2. Frontend Access
```bash
# Open HTML files directly in browser
open index.html
# Or serve with Python
python -m http.server 8080
```

### 3. Backend Services (Optional)
```bash
# Install dependencies
pip install -r requirements.txt

# Start ingest service
cd services/ingest
python main.py
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
├── login.html           # Login page
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
- **Mobile Navigation** - Touch-friendly collapsible sidebar
- **Data Ingestion API** - FastAPI backend for DWLR data collection
- **MQTT Integration** - Real-time device communication support

### 🔄 Backend Services Available
- **Ingest Service** - FastAPI service for data collection
- **Database Schema** - PostgreSQL/TimescaleDB structure
- **Docker Configuration** - Multi-service orchestration
- **MQTT Broker** - Device communication setup

## 🚀 Getting Started

1. **Frontend Only** - Open `index.html` in any modern web browser
2. **With Backend** - Run `python -m http.server 8080` and visit `http://localhost:8080`
3. **Full Stack** - Use `docker-compose up -d` to start all services

## 📄 License

This project is licensed under the MIT License.