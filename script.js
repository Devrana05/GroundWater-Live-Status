// DOM Elements
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebar = document.getElementById('sidebar');
const thresholdSlider = document.getElementById('thresholdSlider');
const thresholdValue = document.getElementById('thresholdValue');
const stationSelect = document.getElementById('stationSelect');

// Current selected station
let selectedStation = 'all';

// API Configuration
const API_BASE_URL = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000/ws';

// WebSocket connection
let websocket = null;

// Chart data cache for fast switching
let chartDataCache = {};

// Sidebar Toggle Functionality
function initSidebarToggle() {
    sidebarToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        if (window.innerWidth > 768) {
            sidebar.classList.toggle('collapsed');
        } else {
            sidebar.classList.toggle('open');
        }
    });
}

// Prevent sidebar expansion on nav link clicks when collapsed
function initNavLinks() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            if (sidebar.classList.contains('collapsed') && window.innerWidth > 768) {
                e.stopPropagation();
                setTimeout(() => {
                    window.location.href = link.href;
                }, 0);
            }
        });
    });
}

initSidebarToggle();
initNavLinks();
initSidebarClose();

// Threshold Slider
thresholdSlider.addEventListener('input', (e) => {
    thresholdValue.textContent = `${e.target.value}m`;
});

// Station Selection
stationSelect.addEventListener('change', (e) => {
    selectedStation = e.target.value;
    updateChartForStationFast(selectedStation);
    updateSummaryForStation(selectedStation);
    
    // Scroll to chart for better UX
    const chartWidget = document.querySelector('.chart-widget');
    if (chartWidget) {
        chartWidget.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'center' 
        });
    }
});

// Initialize Map
let map;
let wellMarkers = {};

async function initMap() {
    map = L.map('map').setView([28.6139, 77.2090], 10);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    // Load wells from API
    await loadWells();
}

async function loadWells() {
    try {
        const response = await fetch(`${API_BASE_URL}/wells`);
        const wells = await response.json();
        
        wells.forEach(well => {
            addWellMarker(well);
        });
    } catch (error) {
        console.error('Error loading wells:', error);
        // Fallback to sample data
        const sampleWells = [
            { well_id: 'ST001', latitude: 28.6139, longitude: 77.2090, current_level: 18.5, device_status: 'online' },
            { well_id: 'ST002', latitude: 28.6289, longitude: 77.2194, current_level: 42.1, device_status: 'online' },
            { well_id: 'ST003', latitude: 28.6089, longitude: 77.1986, current_level: null, device_status: 'offline' }
        ];
        
        sampleWells.forEach(well => addWellMarker(well));
    }
}

function addWellMarker(well) {
    const status = getWellStatus(well);
    const color = getStatusColor(status);
    
    const marker = L.circleMarker([well.latitude, well.longitude], {
        radius: 8,
        fillColor: color,
        color: '#fff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8
    }).addTo(map);
    
    const popupContent = `
        <div style="font-family: Inter, sans-serif;">
            <h4 style="margin: 0 0 8px 0; color: #212121;">${well.well_id}</h4>
            <p style="margin: 4px 0; color: #757575;">
                Level: ${well.current_level ? well.current_level + 'm' : 'No Data'}
            </p>
            <p style="margin: 4px 0; color: #757575;">
                Battery: ${well.battery_level ? well.battery_level + '%' : 'N/A'}
            </p>
            <p style="margin: 4px 0; color: ${color}; font-weight: 500;">
                Status: ${status.charAt(0).toUpperCase() + status.slice(1)}
            </p>
        </div>
    `;
    
    marker.bindPopup(popupContent);
    wellMarkers[well.well_id] = marker;
}

function getWellStatus(well) {
    if (!well.current_level || well.device_status === 'offline') return 'warning';
    if (well.current_level < 20) return 'critical';
    return 'normal';
}

function getStatusColor(status) {
    switch (status) {
        case 'critical': return '#D32F2F';
        case 'warning': return '#FBC02D';
        default: return '#388E3C';
    }
}

// Initialize Chart
let trendChart;

async function initChart() {
    const ctx = document.getElementById('trendChart').getContext('2d');
    
    // Load real data from API
    const chartData = await loadChartData();
    
    trendChart = new Chart(ctx, {
        type: 'line',
        data: chartData,
        options: getChartOptions()
    });
}

async function loadChartData(wellId = null) {
    try {
        if (wellId && wellId !== 'all') {
            // Load data for single well
            const response = await fetch(`${API_BASE_URL}/wells/${wellId}/timeseries?interval=1h`);
            const data = await response.json();
            
            if (data.length > 0) {
                const labels = data.map(d => new Date(d.bucket).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }));
                const datasets = [{
                    label: `Station ${wellId.slice(-3)}`,
                    data: data.map(d => d.avg_level),
                    borderColor: getWellColor(wellId),
                    backgroundColor: getWellColor(wellId, 0.1),
                    borderWidth: 2,
                    fill: false,
                    tension: 0.4
                }];
                
                return { labels, datasets };
            }
        }
        
        // Load data for all wells
        const wells = ['ST001', 'ST002', 'ST003'];
        const datasets = [];
        const labels = [];
        
        for (const wellId of wells) {
            try {
                const response = await fetch(`${API_BASE_URL}/wells/${wellId}/timeseries?interval=1h`);
                const data = await response.json();
                
                if (data.length > 0) {
                    // Use labels from first well
                    if (labels.length === 0) {
                        labels.push(...data.map(d => new Date(d.bucket).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })));
                    }
                    
                    datasets.push({
                        label: `Station ${wellId.slice(-3)}`,
                        data: data.map(d => d.avg_level),
                        borderColor: getWellColor(wellId),
                        backgroundColor: getWellColor(wellId, 0.1),
                        borderWidth: 2,
                        fill: false,
                        tension: 0.4
                    });
                }
            } catch (error) {
                console.error(`Error loading data for ${wellId}:`, error);
            }
        }
        
        // Fallback to sample data if API fails
        if (datasets.length === 0) {
            return getSampleChartData(wellId);
        }
        
        return { labels, datasets };
        
    } catch (error) {
        console.error('Error loading chart data:', error);
        return getSampleChartData(wellId);
    }
}

function getSampleChartData(wellId = null) {
    const labels = [];
    const now = new Date();
    
    for (let i = 23; i >= 0; i--) {
        const time = new Date(now.getTime() - i * 60 * 60 * 1000);
        labels.push(time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }));
    }
    
    if (wellId && wellId !== 'all') {
        // Single station data
        const baseLevel = wellId === 'ST001' ? 18.5 : wellId === 'ST002' ? 42.1 : 35.8;
        const variance = wellId === 'ST001' ? 2 : wellId === 'ST002' ? 3 : 2.5;
        const data = [];
        
        for (let i = 0; i < 24; i++) {
            data.push(baseLevel + Math.random() * variance - variance/2);
        }
        
        return {
            labels,
            datasets: [{
                label: `Station ${wellId.slice(-3)}`,
                data: data,
                borderColor: getWellColor(wellId),
                backgroundColor: getWellColor(wellId, 0.1),
                borderWidth: 2,
                fill: false,
                tension: 0.4
            }]
        };
    }
    
    // All stations data
    const data1 = [];
    const data2 = [];
    const data3 = [];
    
    for (let i = 0; i < 24; i++) {
        data1.push(18.5 + Math.random() * 2 - 1);
        data2.push(42.1 + Math.random() * 3 - 1.5);
        data3.push(35.8 + Math.random() * 2.5 - 1.25);
    }
    
    return {
        labels,
        datasets: [
            {
                label: 'Station 001',
                data: data1,
                borderColor: '#D32F2F',
                backgroundColor: 'rgba(211, 47, 47, 0.1)',
                borderWidth: 2,
                fill: false,
                tension: 0.4
            },
            {
                label: 'Station 002',
                data: data2,
                borderColor: '#388E3C',
                backgroundColor: 'rgba(56, 142, 60, 0.1)',
                borderWidth: 2,
                fill: false,
                tension: 0.4
            },
            {
                label: 'Station 003',
                data: data3,
                borderColor: '#006C86',
                backgroundColor: 'rgba(0, 108, 134, 0.1)',
                borderWidth: 2,
                fill: false,
                tension: 0.4
            }
        ]
    };
}

function getWellColor(wellId, alpha = 1) {
    const colors = {
        'ST001': alpha === 1 ? '#D32F2F' : `rgba(211, 47, 47, ${alpha})`,
        'ST002': alpha === 1 ? '#388E3C' : `rgba(56, 142, 60, ${alpha})`,
        'ST003': alpha === 1 ? '#006C86' : `rgba(0, 108, 134, ${alpha})`
    };
    return colors[wellId] || '#757575';
}

function getChartOptions() {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
                labels: {
                    font: {
                        family: 'Inter'
                    }
                }
            },
            tooltip: {
                mode: 'index',
                intersect: false,
                titleFont: {
                    family: 'Inter'
                },
                bodyFont: {
                    family: 'Inter'
                }
            }
        },
        scales: {
            x: {
                display: true,
                title: {
                    display: true,
                    text: 'Time',
                    font: {
                        family: 'Inter'
                    }
                },
                ticks: {
                    font: {
                        family: 'Inter'
                    }
                }
            },
            y: {
                display: true,
                title: {
                    display: true,
                    text: 'Water Level (m)',
                    font: {
                        family: 'Inter'
                    }
                },
                ticks: {
                    font: {
                        family: 'Inter'
                    }
                }
            }
        },
        interaction: {
            mode: 'nearest',
            axis: 'x',
            intersect: false
        }
    };
}

// WebSocket connection for real-time updates
function initWebSocket() {
    try {
        websocket = new WebSocket(WS_URL);
        
        websocket.onopen = function(event) {
            console.log('WebSocket connected');
        };
        
        websocket.onmessage = function(event) {
            const data = JSON.parse(event.data);
            handleRealTimeUpdate(data);
        };
        
        websocket.onclose = function(event) {
            console.log('WebSocket disconnected');
            // Reconnect after 5 seconds
            setTimeout(initWebSocket, 5000);
        };
        
        websocket.onerror = function(error) {
            console.error('WebSocket error:', error);
        };
    } catch (error) {
        console.error('WebSocket connection failed:', error);
        // Fallback to polling
        setInterval(pollForUpdates, 30000);
    }
}

function handleRealTimeUpdate(data) {
    if (data.type === 'real_time_update' && data.data) {
        // Update chart with new data
        updateChartWithRealTimeData(data.data);
        
        // Update well markers
        updateWellMarkers(data.data);
        
        // Update summary cards
        updateSummaryCards();
    }
}

function updateChartWithRealTimeData(readings) {
    if (!trendChart || readings.length === 0) return;
    
    const now = new Date();
    const timeLabel = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    
    // Group readings by well
    const wellReadings = {};
    readings.forEach(reading => {
        wellReadings[reading.well_id] = reading.water_level;
    });
    
    // Add new data point
    trendChart.data.labels.push(timeLabel);
    
    trendChart.data.datasets.forEach(dataset => {
        const wellId = dataset.label.replace('Station ', 'ST');
        const newValue = wellReadings[wellId] || dataset.data[dataset.data.length - 1];
        dataset.data.push(newValue);
    });
    
    // Remove old data point if more than 24 points
    if (trendChart.data.labels.length > 24) {
        trendChart.data.labels.shift();
        trendChart.data.datasets.forEach(dataset => {
            dataset.data.shift();
        });
    }
    
    trendChart.update('none');
}

function updateWellMarkers(readings) {
    readings.forEach(reading => {
        const marker = wellMarkers[reading.well_id];
        if (marker) {
            // Update marker color based on new reading
            const status = reading.water_level < 20 ? 'critical' : 'normal';
            const color = getStatusColor(status);
            
            marker.setStyle({
                fillColor: color
            });
        }
    });
}

async function pollForUpdates() {
    try {
        const response = await fetch(`${API_BASE_URL}/dashboard/summary`);
        const summary = await response.json();
        updateSummaryCards(summary);
    } catch (error) {
        console.error('Polling error:', error);
    }
}

async function updateSummaryCards(summary = null) {
    if (!summary) {
        try {
            const response = await fetch(`${API_BASE_URL}/dashboard/summary`);
            summary = await response.json();
        } catch (error) {
            console.error('Error fetching summary:', error);
            return;
        }
    }
    
    // Update summary card values
    const avgDepthElement = document.querySelector('.summary-card .metric');
    if (avgDepthElement && summary.avg_current_level) {
        avgDepthElement.textContent = `${summary.avg_current_level.toFixed(1)}m`;
    }
}

// Mobile sidebar handling
function handleMobileMenu() {
    if (window.innerWidth <= 768) {
        document.addEventListener('click', closeSidebarOutside);
    } else {
        document.removeEventListener('click', closeSidebarOutside);
    }
}

function closeSidebarOutside(e) {
    if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
        sidebar.classList.remove('open');
    }
}

// Sidebar close button
function initSidebarClose() {
    const sidebarClose = document.getElementById('sidebarClose');
    if (sidebarClose) {
        sidebarClose.addEventListener('click', () => {
            sidebar.classList.remove('open');
        });
    }
}

// Table interactions
function initTableInteractions() {
    const tableRows = document.querySelectorAll('.data-table tbody tr');
    
    tableRows.forEach(row => {
        row.addEventListener('click', () => {
            // Remove previous selection
            tableRows.forEach(r => r.classList.remove('selected'));
            // Add selection to clicked row
            row.classList.add('selected');
            
            // Add selected row styling
            row.style.backgroundColor = 'rgba(0, 108, 134, 0.1)';
            row.style.borderLeft = '3px solid #006C86';
        });
    });
}

// Export functionality
function initExportButtons() {
    const exportButtons = document.querySelectorAll('.export-btn');
    
    exportButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Simulate export
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Exporting...';
            
            setTimeout(() => {
                btn.innerHTML = '<i class="fas fa-check"></i> Exported';
                
                setTimeout(() => {
                    if (btn.textContent.includes('CSV')) {
                        btn.innerHTML = '<i class="fas fa-file-csv"></i> Export CSV';
                    } else {
                        btn.innerHTML = '<i class="fas fa-download"></i>';
                    }
                }, 2000);
            }, 1500);
        });
    });
}

// Alert interactions
function initAlertInteractions() {
    const alertActions = document.querySelectorAll('.alert-action');
    
    alertActions.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            
            // Add ripple effect
            btn.style.transform = 'scale(0.95)';
            setTimeout(() => {
                btn.style.transform = 'scale(1)';
            }, 150);
            
            // Simulate action
            const icon = btn.querySelector('i');
            const originalClass = icon.className;
            icon.className = 'fas fa-spinner fa-spin';
            
            setTimeout(() => {
                icon.className = 'fas fa-check';
                setTimeout(() => {
                    icon.className = originalClass;
                }, 2000);
            }, 1000);
        });
    });
}

// Notification interactions
let notificationListenersAdded = false;

function initNotifications() {
    const notificationBtn = document.getElementById('notificationBtn');
    const notificationPopup = document.getElementById('notificationPopup');
    const closePopup = document.getElementById('closePopup');
    
    if (notificationBtn && notificationPopup && !notificationListenersAdded) {
        notificationBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            notificationPopup.classList.toggle('show');
        });
        
        if (closePopup) {
            closePopup.addEventListener('click', () => {
                notificationPopup.classList.remove('show');
            });
        }
        
        document.addEventListener('click', (e) => {
            if (!notificationPopup.contains(e.target) && !notificationBtn.contains(e.target)) {
                notificationPopup.classList.remove('show');
            }
        });
        
        notificationListenersAdded = true;
    }
}

// Clear all notifications function
function clearAllNotifications() {
    const notificationBadge = document.querySelector('.notification-badge');
    const popupContent = document.querySelector('.popup-content');
    
    if (notificationBadge) {
        notificationBadge.textContent = '0';
        notificationBadge.style.display = 'none';
    }
    
    if (popupContent) {
        popupContent.innerHTML = '<p style="text-align: center; color: #757575; padding: 20px;">No active alerts</p>';
    }
    
    localStorage.setItem('notificationsCleared', 'true');
    
    const notificationPopup = document.getElementById('notificationPopup');
    if (notificationPopup) {
        notificationPopup.classList.remove('show');
    }
}

// Resize handler
function handleResize() {
    window.addEventListener('resize', () => {
        if (map) {
            setTimeout(() => {
                map.invalidateSize();
            }, 100);
        }
        
        handleMobileMenu();
    });
}

// Load alerts from API
async function loadAlerts() {
    try {
        const response = await fetch(`${API_BASE_URL}/alerts?active_only=true`);
        const alerts = await response.json();
        
        // Update alert count
        const alertCountElement = document.querySelector('.alert-count');
        if (alertCountElement) {
            alertCountElement.textContent = alerts.length;
        }
        
        // Update notification badge
        const notificationBadge = document.querySelector('.notification-badge');
        if (notificationBadge) {
            notificationBadge.textContent = alerts.length;
            notificationBadge.style.display = alerts.length > 0 ? 'block' : 'none';
        }
        
    } catch (error) {
        console.error('Error loading alerts:', error);
    }
}

// Fast chart update using cached data
function updateChartForStationFast(stationId) {
    if (!trendChart) return;
    
    // Use cached data if available
    if (chartDataCache[stationId]) {
        trendChart.data = chartDataCache[stationId];
        trendChart.update();
        updateChartTitle(stationId);
        return;
    }
    
    // Load and cache data if not available
    loadChartData(stationId).then(chartData => {
        chartDataCache[stationId] = chartData;
        trendChart.data = chartData;
        trendChart.update();
        updateChartTitle(stationId);
    });
}

// Update chart title
function updateChartTitle(stationId) {
    const chartTitle = document.getElementById('chartTitle');
    if (chartTitle) {
        chartTitle.textContent = stationId === 'all' ? 
            'Water Level Trends - All Stations' : 
            `Water Level Trends - Station ${stationId.slice(-3)}`;
    }
}

// Preload all chart data for instant switching
async function preloadChartData() {
    try {
        // Try bulk endpoint first for faster loading
        const response = await fetch(`${API_BASE_URL}/wells/timeseries/bulk?interval=1h`);
        if (response.ok) {
            const bulkData = await response.json();
            
            // Process bulk data into chart format
            const stations = ['ST001', 'ST002', 'ST003'];
            const labels = [];
            const allStationData = [];
            
            // Create labels from first station
            if (bulkData['ST001'] && bulkData['ST001'].length > 0) {
                labels.push(...bulkData['ST001'].map(d => 
                    new Date(d.bucket).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
                ));
            }
            
            // Create datasets for each station
            stations.forEach(stationId => {
                if (bulkData[stationId]) {
                    const data = bulkData[stationId].map(d => d.avg_level);
                    chartDataCache[stationId] = {
                        labels: labels,
                        datasets: [{
                            label: `Station ${stationId.slice(-3)}`,
                            data: data,
                            borderColor: getWellColor(stationId),
                            backgroundColor: getWellColor(stationId, 0.1),
                            borderWidth: 2,
                            fill: false,
                            tension: 0.4
                        }]
                    };
                    allStationData.push({
                        label: `Station ${stationId.slice(-3)}`,
                        data: data,
                        borderColor: getWellColor(stationId),
                        backgroundColor: getWellColor(stationId, 0.1),
                        borderWidth: 2,
                        fill: false,
                        tension: 0.4
                    });
                }
            });
            
            // Create 'all' stations view
            chartDataCache['all'] = {
                labels: labels,
                datasets: allStationData
            };
            
            return; // Success, exit early
        }
    } catch (error) {
        console.log('Bulk endpoint failed, falling back to individual requests:', error);
    }
    
    // Fallback to individual requests
    const stations = ['all', 'ST001', 'ST002', 'ST003'];
    for (const stationId of stations) {
        try {
            chartDataCache[stationId] = await loadChartData(stationId);
        } catch (error) {
            console.error(`Failed to preload data for ${stationId}:`, error);
        }
    }
}

// Update summary for selected station
async function updateSummaryForStation(stationId) {
    const summaryTitle = document.getElementById('summaryTitle');
    const currentLevel = document.getElementById('currentLevel');
    const levelChange = document.getElementById('levelChange');
    const batteryLevel = document.getElementById('batteryLevel');
    const batteryStatus = document.getElementById('batteryStatus');
    const lastReading = document.getElementById('lastReading');
    const deviceStatus = document.getElementById('deviceStatus');
    
    if (stationId === 'all') {
        summaryTitle.textContent = 'Resource Summary';
        currentLevel.textContent = '45.2m';
        levelChange.textContent = '+2.1%';
        levelChange.className = 'change positive';
        batteryLevel.textContent = '85%';
        batteryStatus.textContent = 'Good';
        lastReading.textContent = '2 min ago';
        deviceStatus.textContent = 'Online';
    } else {
        try {
            const response = await fetch(`${API_BASE_URL}/wells`);
            const wells = await response.json();
            const well = wells.find(w => w.well_id === stationId);
            
            if (well) {
                summaryTitle.textContent = `Station ${stationId.slice(-3)} Summary`;
                currentLevel.textContent = well.current_level ? `${well.current_level}m` : 'No Data';
                batteryLevel.textContent = well.battery_level ? `${well.battery_level}%` : 'N/A';
                
                // Set status colors
                if (well.current_level < 20) {
                    levelChange.className = 'change negative';
                    levelChange.textContent = 'Critical';
                } else if (well.current_level < 30) {
                    levelChange.className = 'change warning';
                    levelChange.textContent = 'Warning';
                } else {
                    levelChange.className = 'change positive';
                    levelChange.textContent = 'Normal';
                }
                
                batteryStatus.textContent = well.battery_level > 20 ? 'Good' : 'Low';
                deviceStatus.textContent = well.device_status || 'Online';
                lastReading.textContent = well.last_reading ? 
                    formatTimestamp(well.last_reading) : '2 min ago';
            }
        } catch (error) {
            console.error('Error loading well data:', error);
            // Use sample data
            const sampleData = {
                'ST001': { level: '18.5m', battery: '85%', status: 'Critical' },
                'ST002': { level: '42.1m', battery: '92%', status: 'Normal' },
                'ST003': { level: 'No Data', battery: '78%', status: 'Warning' }
            };
            
            const data = sampleData[stationId];
            if (data) {
                summaryTitle.textContent = `Station ${stationId.slice(-3)} Summary`;
                currentLevel.textContent = data.level;
                batteryLevel.textContent = data.battery;
                levelChange.textContent = data.status;
                levelChange.className = `change ${data.status.toLowerCase()}`;
            }
        }
    }
}

// Theme toggle functionality
function initThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    const savedTheme = localStorage.getItem('theme');
    
    // Apply saved theme and sync slider
    if (savedTheme === 'dark') {
        document.documentElement.classList.add('dark-theme');
        if (themeToggle) themeToggle.checked = true;
    } else {
        document.documentElement.classList.remove('dark-theme');
        if (themeToggle) themeToggle.checked = false;
    }
    
    // Theme toggle event listener
    if (themeToggle) {
        themeToggle.addEventListener('change', () => {
            if (themeToggle.checked) {
                document.documentElement.classList.add('dark-theme');
                localStorage.setItem('theme', 'dark');
            } else {
                document.documentElement.classList.remove('dark-theme');
                localStorage.setItem('theme', 'light');
            }
        });
    }
}

// Profile button functionality
function initProfileButton() {
    const profileBtn = document.getElementById('profileBtn');
    const profilePopup = document.getElementById('profilePopup');
    const profileSettings = document.getElementById('profileSettings');
    const logoutBtn = document.getElementById('logoutBtn');
    
    if (profileBtn && profilePopup) {
        profileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            profilePopup.classList.toggle('show');
        });
        
        // Close popup when clicking outside
        document.addEventListener('click', (e) => {
            if (!profilePopup.contains(e.target) && !profileBtn.contains(e.target)) {
                profilePopup.classList.remove('show');
            }
        });
    }
    
    if (profileSettings) {
        profileSettings.addEventListener('click', () => {
            alert('Profile Settings clicked! Add settings functionality here.');
            profilePopup.classList.remove('show');
        });
    }
    
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('isLoggedIn');
            localStorage.removeItem('username');
            window.location.href = 'login.html';
        });
    }
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
    initThemeToggle();
    await initMap();
    await initChart();
    
    // Preload chart data for fast switching
    await preloadChartData();
    
    initTableInteractions();
    initExportButtons();
    initAlertInteractions();
    initNotifications();
    initProfileButton();
    handleMobileMenu();
    handleResize();
    
    // Initialize WebSocket for real-time updates
    initWebSocket();
    
    // Load initial dashboard data
    await updateSummaryCards();
    await loadAlerts();
});

// Add CSS for selected table row and animations
const style = document.createElement('style');
style.textContent = `
    .data-table tbody tr.selected {
        background-color: rgba(0, 108, 134, 0.1) !important;
        border-left: 3px solid #006C86;
    }
    
    @keyframes fadeOut {
        from { opacity: 1; transform: scale(1); }
        to { opacity: 0; transform: scale(0.8); }
    }
    
    .notification-badge {
        animation: pulse 2s infinite;
    }
    
    .live-indicator i {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
`;
document.head.appendChild(style);

// Navigate to specific alert
function navigateToAlert(alertId) {
    // Store alert ID in localStorage to highlight it on alerts page
    localStorage.setItem('highlightAlert', alertId);
    // Navigate to alerts page
    window.location.href = 'alerts.html';
}

// Make functions globally available
window.clearAllNotifications = clearAllNotifications;
window.navigateToAlert = navigateToAlert;

// Utility functions
function formatTimestamp(timestamp) {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now - time;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)} hr ago`;
    return time.toLocaleDateString();
}

function formatNumber(num, decimals = 1) {
    return num ? num.toFixed(decimals) : 'N/A';
}