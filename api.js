// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// API Client
class APIClient {
    constructor() {
        this.baseURL = API_BASE_URL;
        this.token = localStorage.getItem('auth_token');
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        if (this.token) {
            config.headers.Authorization = `Bearer ${this.token}`;
        }

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                if (response.status === 401) {
                    this.logout();
                    return null;
                }
                throw new Error(`HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.warn(`API request failed: ${error.message}`);
            return this.getFallbackData(endpoint);
        }
    }

    getFallbackData(endpoint) {
        // Demo data fallbacks
        const fallbacks = {
            '/wells': [
                { well_id: 'ST001', name: 'Station 001', latitude: 28.6139, longitude: 77.2090, current_level: 45.2, status: 'normal' },
                { well_id: 'ST002', name: 'Station 002', latitude: 28.6129, longitude: 77.2290, current_level: 32.1, status: 'warning' },
                { well_id: 'ST003', name: 'Station 003', latitude: 28.6149, longitude: 77.1990, current_level: 18.5, status: 'critical' }
            ],
            '/dashboard/summary': {
                total_wells: 3,
                active_wells: 3,
                avg_current_level: 31.9,
                active_alerts: 2,
                avg_24h_change: -1.2
            },
            '/alerts': [
                { id: 1, well_id: 'ST001', severity: 'critical', message: 'Critical water level', created_at: new Date().toISOString() },
                { id: 2, well_id: 'ST002', severity: 'warning', message: 'Low battery', created_at: new Date().toISOString() }
            ]
        };

        return fallbacks[endpoint] || {};
    }

    async login(username, password) {
        const response = await this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });

        if (response?.access_token) {
            this.token = response.access_token;
            localStorage.setItem('auth_token', this.token);
            return response;
        }

        // Demo login fallback
        if (username === 'admin' && password === 'admin123') {
            this.token = 'demo_token';
            localStorage.setItem('auth_token', this.token);
            return {
                access_token: 'demo_token',
                user: { username: 'admin', full_name: 'Administrator', role: 'admin' }
            };
        }

        throw new Error('Invalid credentials');
    }

    logout() {
        this.token = null;
        localStorage.removeItem('auth_token');
        window.location.href = 'login.html';
    }

    async getWells() {
        return await this.request('/wells');
    }

    async getDashboardSummary() {
        return await this.request('/dashboard/summary');
    }

    async getAlerts() {
        return await this.request('/alerts');
    }

    async getWellTimeseries(wellId, startDate, endDate) {
        const params = new URLSearchParams();
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        
        return await this.request(`/wells/${wellId}/timeseries?${params}`);
    }

    async getBulkTimeseries(startDate, endDate) {
        const params = new URLSearchParams();
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        
        return await this.request(`/wells/timeseries/bulk?${params}`);
    }
}

// Global API instance
window.api = new APIClient();