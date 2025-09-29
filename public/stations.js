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

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initThemeToggle();
    initSidebarToggle();
    handleMobileMenu();
    handleResize();
    initProfileButton();
});