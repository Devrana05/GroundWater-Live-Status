# Groundwater Real-Time Monitoring System

A complete end-to-end solution for real-time groundwater resource evaluation using Digital Water Level Recorder (DWLR) data.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ (for backend)
- Web Browser (Chrome, Firefox, Safari)

### 1. Clone Repository
```bash
git clone https://github.com/your-username/groundwater-monitoring-system.git
cd groundwater-monitoring-system
```

### 2. Run Complete System (Recommended)

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

### 3. Manual Setup

**Backend:**
```bash
cd services/api
pip install -r requirements.txt
python main.py
```

**Frontend:**
```bash
python -m http.server 8080
```

## 🌐 Access Points

- **Web Dashboard**: http://localhost:8080
- **API Documentation**: http://localhost:8000/docs
- **Login Credentials**: admin / admin123

## 📊 Features

### Frontend Dashboard
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Dark/Light Theme** - Dynamic theme switching with persistence
- **Interactive Maps** - Station locations with status indicators
- **Real-time Charts** - Water level trends with instant switching
- **Alert Management** - Cross-page notification system
- **Data Filtering** - Station and status-based filtering
- **Forecasting** - ML-powered groundwater level predictions

### Backend API
- **FastAPI** - Modern, fast web framework
- **Authentication** - JWT-based security
- **Real-time Data** - WebSocket support
- **Caching** - Redis integration for performance
- **Database** - PostgreSQL/TimescaleDB support

## 🛠️ Technologies

### Frontend
- HTML5, CSS3, JavaScript (ES6)
- Chart.js for data visualization
- Leaflet.js for interactive maps
- Font Awesome icons

### Backend
- Python 3.8+ with FastAPI
- Optional: PostgreSQL, Redis, JWT libraries
- Fallback demo mode when dependencies unavailable

## 📁 Project Structure

```
SIH/
├── services/api/        # FastAPI backend
├── *.html              # Frontend pages
├── *.css               # Stylesheets
├── *.js                # JavaScript files
├── start.bat           # Windows startup script
├── start.sh            # Linux/Mac startup script
└── README.md
```

## 🎯 Pages

1. **Login** - Authentication with admin/admin123
2. **Dashboard** - Overview with maps and charts
3. **Data Explorer** - Filterable data tables
4. **Alerts** - Alert management with filtering
5. **Stations** - Station monitoring
6. **Forecasting** - ML-powered predictions

## 📚 API Endpoints

- `GET /wells` - Get all wells data
- `GET /dashboard/summary` - Dashboard statistics
- `GET /alerts` - Active alerts
- `GET /wells/{id}/timeseries` - Time series data
- `POST /auth/login` - User authentication

## 🔧 Development

The system includes fallback demo data when backend is unavailable, making it perfect for development and demonstrations.

## 📄 License

MIT License