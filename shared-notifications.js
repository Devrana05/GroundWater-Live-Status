// Shared notification functionality for all pages
let sharedNotificationListenersAdded = false;

function initNotifications() {
    const notificationBtn = document.getElementById('notificationBtn');
    const notificationPopup = document.getElementById('notificationPopup');
    const closePopup = document.getElementById('closePopup');
    
    if (notificationBtn && notificationPopup && !sharedNotificationListenersAdded) {
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
        
        sharedNotificationListenersAdded = true;
    }
}

// Navigate to specific alert
function navigateToAlert(alertId) {
    // Reduce notification count
    updateNotificationCount(-1);
    
    localStorage.setItem('highlightAlert', alertId);
    window.location.href = 'alerts.html';
}

// Update notification count
function updateNotificationCount(change) {
    const badges = document.querySelectorAll('.notification-badge');
    badges.forEach(badge => {
        let currentCount = parseInt(badge.textContent) || 0;
        let newCount = Math.max(0, currentCount + change);
        badge.textContent = newCount;
        badge.style.display = newCount > 0 ? 'block' : 'none';
    });
}

// Initialize notification count based on actual alerts
function initNotificationCount() {
    const alertElements = document.querySelectorAll('.popup-alert');
    const alertCount = alertElements.length;
    
    const badges = document.querySelectorAll('.notification-badge');
    badges.forEach(badge => {
        badge.textContent = alertCount;
        badge.style.display = alertCount > 0 ? 'block' : 'none';
    });
}

// Clear all notifications
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

// Make functions globally available
window.clearAllNotifications = clearAllNotifications;
window.navigateToAlert = navigateToAlert;

// Apply notification cleared state
function applyNotificationState() {
    const isCleared = localStorage.getItem('notificationsCleared') === 'true';
    
    if (isCleared) {
        // Hide all popup alerts
        const alertElements = document.querySelectorAll('.popup-alert');
        alertElements.forEach(alert => {
            alert.style.display = 'none';
        });
        
        // Set notification count to zero
        const badges = document.querySelectorAll('.notification-badge');
        badges.forEach(badge => {
            badge.textContent = '0';
            badge.style.display = 'none';
        });
        
        // Update alert count in dashboard if present
        const alertCount = document.querySelector('.alert-count');
        if (alertCount) {
            alertCount.textContent = '0';
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

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    initNotifications();
    initNotificationCount();
    applyNotificationState();
    initThemeToggle();
});