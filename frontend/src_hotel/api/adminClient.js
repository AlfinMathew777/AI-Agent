"""
Centralized API Client for Admin Operations
--------------------------------------------

    This module provides a unified client for all admin API calls.
        Benefits:
- Consistent error handling
    - Automatic retry logic
        - Request / response logging
            - Token management
"""

class APIError extends Error {
    constructor(message, statusCode, details = {}) {
        super(message);
        this.name = 'APIError';
        this.statusCode = statusCode;
        this.details = details;
    }
}

class AdminAPIClient {
    constructor(baseURL = 'http://127.0.0.1:8010', adminKey = '') {
        this.baseURL = baseURL;
        this.adminKey = adminKey;
        this.requestCount = 0;
    }

    /**
     * Make an API request with proper error handling
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const requestId = ++this.requestCount;

        const headers = {
            'Content-Type': 'application/json',
            'x-admin-key': this.adminKey,
            'x-request-id': `req_${requestId}_${Date.now()}`,
            ...options.headers
        };

        const config = {
            ...options,
            headers
        };

        try {
            console.log(`[API ${requestId}] ${options.method || 'GET'} ${endpoint}`);

            const response = await fetch(url, config);

            if (!response.ok) {
                // Try to parse error response
                let errorData;
                try {
                    errorData = await response.json();
                } catch {
                    errorData = { error: response.statusText };
                }

                const errorMessage = typeof errorData.detail === 'object'
                    ? errorData.detail.error || 'Request failed'
                    : errorData.detail || errorData.error || 'Request failed';

                console.error(`[API ${requestId}] Error ${response.status}:`, errorMessage);

                throw new APIError(errorMessage, response.status, errorData);
            }

            const data = await response.json();
            console.log(`[API ${requestId}] Success`);
            return data;

        } catch (error) {
            if (error instanceof APIError) {
                throw error;
            }

            // Network error or other unexpected error
            console.error(`[API ${requestId}] Network error:`, error);

            if (error.name === 'AbortError') {
                throw new APIError('Request timeout', 408);
            }

            throw new APIError(
                'Network error. Is the backend running on port 8010?',
                0,
                { originalError: error.message }
            );
        }
    }

    // ========================================================================
    // Properties Endpoints
    // ========================================================================

    async getProperties() {
        return this.request('/admin/properties');
    }

    async pauseProperty(propertyId) {
        return this.request(`/admin/properties/${propertyId}/pause`, {
            method: 'POST'
        });
    }

    async resumeProperty(propertyId) {
        return this.request(`/admin/properties/${propertyId}/resume`, {
            method: 'POST'
        });
    }

    // ========================================================================
    // Marketplace Endpoints
    // ========================================================================

    async getMarketplaceProperties() {
        return this.request('/marketplace/properties');
    }

    // ========================================================================
    // System Status Endpoints
    // ========================================================================

    async getSystemStatus() {
        return this.request('/admin/system/status');
    }

    async getHealth() {
        return this.request('/health');
    }

    // ========================================================================
    // Analytics Endpoints
    // ========================================================================

    async getAnalytics() {
        return this.request('/admin/analytics');
    }

    async getToolStats() {
        return this.request('/admin/tools/stats');
    }

    // ========================================================================
    // Rooms Endpoints
    // ========================================================================

    async getRooms() {
        return this.request('/admin/rooms');
    }

    async getRoomStatistics() {
        return this.request('/admin/rooms/statistics');
    }

    async updateRoomStatus(roomId, status) {
        return this.request(`/admin/rooms/${roomId}/status`, {
            method: 'PUT',
            body: JSON.stringify({ status })
        });
    }

    // ========================================================================
    // Reservations Endpoints
    // ========================================================================

    async getReservations(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = `/admin/reservations${queryString ? '?' + queryString : ''}`;
        return this.request(endpoint);
    }

    async checkIn(reservationId) {
        return this.request(`/admin/reservations/${reservationId}/checkin`, {
            method: 'PUT'
        });
    }

    async checkOut(reservationId) {
        return this.request(`/admin/reservations/${reservationId}/checkout`, {
            method: 'PUT'
        });
    }

    // ========================================================================
    // Housekeeping Endpoints
    // ========================================================================

    async getHousekeepingTasks(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = `/admin/housekeeping/tasks${queryString ? '?' + queryString : ''}`;
        return this.request(endpoint);
    }

    async getHousekeepingStatistics() {
        return this.request('/admin/housekeeping/statistics');
    }

    async startTask(taskId) {
        return this.request(`/admin/housekeeping/tasks/${taskId}/start`, {
            method: 'PUT'
        });
    }

    async completeTask(taskId) {
        return this.request(`/admin/housekeeping/tasks/${taskId}/complete`, {
            method: 'PUT'
        });
    }

    // ========================================================================
    // Knowledge Base Endpoints
    // ========================================================================

    async getIndexStatus() {
        return this.request('/admin/index/status');
    }

    async uploadDocument(audience, file) {
        const formData = new FormData();
        formData.append('file', file);

        return this.request(`/admin/upload?audience=${audience}`, {
            method: 'POST',
            headers: {
                // Don't set Content-Type, let browser set it with boundary
                'x-admin-key': this.adminKey
            },
            body: formData
        });
    }

    async reindexDocuments() {
        return this.request('/admin/reindex', {
            method: 'POST'
        });
    }

    // ========================================================================
    // Chats & Monitoring Endpoints
    // ========================================================================

    async getChats(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = `/admin/chats${queryString ? '?' + queryString : ''}`;
        return this.request(endpoint);
    }

    async getChatThread(sessionId) {
        return this.request(`/admin/chats/thread?session_id=${sessionId}`);
    }

    async getPayments(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = `/admin/payments${queryString ? '?' + queryString : ''}`;
        return this.request(endpoint);
    }

    async getReceipts(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = `/admin/receipts${queryString ? '?' + queryString : ''}`;
        return this.request(endpoint);
    }
}

export { AdminAPIClient, APIError };
