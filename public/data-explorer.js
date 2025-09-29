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

// Station data
const stationData = {
    'all': [
        {id:'ST001',timestamp:'2024-01-15 14:30:00',level:18.5,battery:85.2,temp:22.1,status:'critical',quality:'good'},
        {id:'ST002',timestamp:'2024-01-15 14:29:45',level:42.1,battery:92.1,temp:21.8,status:'normal',quality:'good'},
        {id:'ST003',timestamp:'2024-01-15 14:00:12',level:null,battery:78.5,temp:null,status:'warning',quality:'poor'}
    ],
    'ST001': [
        {id:'ST001',timestamp:'2024-01-15 14:30:00',level:18.5,battery:85.2,temp:22.1,status:'critical',quality:'good'},
        {id:'ST001',timestamp:'2024-01-15 13:30:00',level:18.7,battery:85.5,temp:22.3,status:'critical',quality:'good'}
    ],
    'ST002': [
        {id:'ST002',timestamp:'2024-01-15 14:29:45',level:42.1,battery:92.1,temp:21.8,status:'normal',quality:'good'},
        {id:'ST002',timestamp:'2024-01-15 13:29:45',level:42.3,battery:92.3,temp:21.9,status:'normal',quality:'good'}
    ],
    'ST003': [
        {id:'ST003',timestamp:'2024-01-15 14:00:12',level:null,battery:78.5,temp:null,status:'warning',quality:'poor'}
    ]
};

// Filter functionality
function initStationFilter() {
    const stationFilter = document.getElementById('stationFilter');
    const statusFilter = document.getElementById('statusFilter');
    if (stationFilter) stationFilter.addEventListener('change', updateData);
    if (statusFilter) statusFilter.addEventListener('change', updateData);
}

function updateData() {
    const selectedStation = document.getElementById('stationFilter').value;
    const selectedStatus = document.getElementById('statusFilter').value;
    let data = stationData[selectedStation] || stationData['all'];
    
    // Filter by status
    if (selectedStatus !== 'all') {
        data = data.filter(d => d.status === selectedStatus);
    }
    
    // Update overview cards
    const critical = data.filter(d => d.status === 'critical').length;
    const warning = data.filter(d => d.status === 'warning').length;
    const normal = data.filter(d => d.status === 'normal').length;
    
    document.querySelector('.overview-card.critical .count').textContent = critical;
    document.querySelector('.overview-card.warning .count').textContent = warning;
    document.querySelector('.overview-card.normal .count').textContent = normal;
    document.querySelector('.overview-card.total .count').textContent = data.length;
    
    // Update data table
    const tbody = document.getElementById('dataTableBody');
    tbody.innerHTML = '';
    
    if (data.length === 0) {
        const tr = document.createElement('tr');
        tr.innerHTML = '<td colspan="8" style="text-align:center;padding:20px;color:var(--text-secondary)">No data available for selected filters</td>';
        tbody.appendChild(tr);
    } else {
        data.forEach(row => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${row.id}</td>
                <td>${row.timestamp}</td>
                <td>${row.level || '--'}</td>
                <td>${row.battery}</td>
                <td>${row.temp || '--'}</td>
                <td><span class="status ${row.status}">${row.status.charAt(0).toUpperCase() + row.status.slice(1)}</span></td>
                <td><span class="quality-flag ${row.quality}">${row.quality.charAt(0).toUpperCase() + row.quality.slice(1)}</span></td>
                <td>
                    <button class="action-btn view" title="View Details"><i class="fas fa-eye"></i></button>
                    <button class="action-btn edit" title="Edit"><i class="fas fa-edit"></i></button>
                </td>
            `;
            tbody.appendChild(tr);
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

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initThemeToggle();
    initSidebarToggle();
    handleMobileMenu();
    handleResize();
    initStationFilter();
    initProfileButton();
});