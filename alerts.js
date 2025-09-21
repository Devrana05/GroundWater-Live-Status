// DOM Elements
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebar = document.getElementById('sidebar');

// Sidebar Toggle Functionality
function initSidebarToggle() {
    if (window.innerWidth > 768) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
        });
    }
}

// Mobile sidebar handling
function handleMobileMenu() {
    // Remove existing listeners
    sidebarToggle.removeEventListener('click', toggleSidebar);
    document.removeEventListener('click', closeSidebarOutside);
    
    if (window.innerWidth <= 768) {
        sidebarToggle.addEventListener('click', toggleSidebar);
        document.addEventListener('click', closeSidebarOutside);
    }
}

function toggleSidebar(e) {
    e.stopPropagation();
    sidebar.classList.toggle('open');
}

function closeSidebarOutside(e) {
    if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
        sidebar.classList.remove('open');
    }
}

// Resize handler
function handleResize() {
    window.addEventListener('resize', () => {
        handleMobileMenu();
    });
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
        
        document.addEventListener('click', (e) => {
            if (!profilePopup.contains(e.target) && !profileBtn.contains(e.target)) {
                profilePopup.classList.remove('show');
            }
        });
    }
    
    if (profileSettings) {
        profileSettings.addEventListener('click', () => {
            alert('Profile Settings clicked!');
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

// Check for highlighted alert on page load
document.addEventListener('DOMContentLoaded', () => {
    // Initialize theme and sidebar
    initThemeToggle();
    initSidebarToggle();
    handleMobileMenu();
    handleResize();
    initProfileButton();
    
    // Initialize map
    initMap();
    
    // Initialize filters
    initFilters();
    
    const highlightAlert = localStorage.getItem('highlightAlert');
    
    if (highlightAlert) {
        // Find and highlight the specific alert
        const alertCard = document.querySelector(`[data-alert-id="${highlightAlert}"]`);
        
        if (alertCard) {
            // Add highlight class
            alertCard.classList.add('highlighted');
            
            // Scroll to the alert
            setTimeout(() => {
                alertCard.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'center' 
                });
            }, 500);
            
            // Remove highlight after 3 seconds
            setTimeout(() => {
                alertCard.classList.remove('highlighted');
            }, 3000);
        }
        
        // Clear the stored alert ID
        localStorage.removeItem('highlightAlert');
    }
});

// Initialize filters
function initFilters() {
    const severityFilter = document.getElementById('severityFilter');
    const stationFilter = document.getElementById('stationFilter');
    
    if (severityFilter) {
        severityFilter.addEventListener('change', filterAlerts);
    }
    
    if (stationFilter) {
        stationFilter.addEventListener('change', filterAlerts);
    }
}

// Filter alerts based on selected criteria
function filterAlerts() {
    const severityFilter = document.getElementById('severityFilter');
    const stationFilter = document.getElementById('stationFilter');
    const alertCards = document.querySelectorAll('.alert-card');
    const alertsContainer = document.querySelector('.alerts-container');
    
    const selectedSeverity = severityFilter ? severityFilter.value : 'all';
    const selectedStation = stationFilter ? stationFilter.value : 'all';
    
    let visibleCount = 0;
    
    alertCards.forEach(card => {
        const cardSeverity = card.classList.contains('critical') ? 'critical' : 
                           card.classList.contains('warning') ? 'warning' : 'normal';
        const cardStation = card.getAttribute('data-station');
        
        const severityMatch = selectedSeverity === 'all' || cardSeverity === selectedSeverity;
        const stationMatch = selectedStation === 'all' || cardStation === selectedStation;
        
        if (severityMatch && stationMatch) {
            card.style.display = 'block';
            visibleCount++;
        } else {
            card.style.display = 'none';
        }
    });
    
    // Show/hide no alerts message
    showNoAlertsMessage(visibleCount === 0, selectedSeverity, selectedStation);
}

// Show no alerts message when no alerts match filters
function showNoAlertsMessage(show, severity, station) {
    const alertsContainer = document.querySelector('.alerts-container');
    let noAlertsMsg = document.querySelector('.no-alerts-message');
    
    if (show) {
        if (!noAlertsMsg) {
            noAlertsMsg = document.createElement('div');
            noAlertsMsg.className = 'no-alerts-message';
            alertsContainer.appendChild(noAlertsMsg);
        }
        
        let message = 'No alerts found';
        if (severity !== 'all' && station !== 'all') {
            message = `No ${severity} alerts found for ${station}`;
        } else if (severity !== 'all') {
            message = `No ${severity} alerts found`;
        } else if (station !== 'all') {
            message = `No alerts found for ${station}`;
        }
        
        noAlertsMsg.innerHTML = `
            <div class="no-alerts-content">
                <i class="fas fa-info-circle"></i>
                <h3>${message}</h3>
                <p>Try adjusting your filters to see more alerts</p>
            </div>
        `;
        noAlertsMsg.style.display = 'flex';
    } else {
        if (noAlertsMsg) {
            noAlertsMsg.style.display = 'none';
        }
    }
}

// Initialize Map
let map;
let wellMarkers = {};

async function initMap() {
    map = L.map('map').setView([28.6139, 77.2090], 10);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    // Load wells with alert status
    await loadWells();
}

async function loadWells() {
    // Sample wells data with alert status
    const sampleWells = [
        { well_id: 'ST001', latitude: 28.6139, longitude: 77.2090, current_level: 18.5, device_status: 'online', alert_status: 'critical' },
        { well_id: 'ST002', latitude: 28.6289, longitude: 77.2194, current_level: 42.1, device_status: 'online', alert_status: 'warning' },
        { well_id: 'ST003', latitude: 28.6089, longitude: 77.1986, current_level: null, device_status: 'offline', alert_status: 'normal' }
    ];
    
    sampleWells.forEach(well => addWellMarker(well));
}

function addWellMarker(well) {
    const status = well.alert_status || getWellStatus(well);
    const color = getStatusColor(status);
    
    const marker = L.circleMarker([well.latitude, well.longitude], {
        radius: 10,
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