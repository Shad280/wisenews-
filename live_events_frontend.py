"""
Enhanced Live Events Frontend Integration
JavaScript components for real-time updates and improved UX
"""

# Enhanced JavaScript for live events (to be included in templates)
ENHANCED_LIVE_EVENTS_JS = """
class LiveEventsManager {
    constructor() {
        this.socket = null;
        this.subscribedEvents = new Set();
        this.eventData = new Map();
        this.updateHistory = new Map();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        
        this.initializeSocket();
        this.setupEventHandlers();
    }
    
    initializeSocket() {
        // Initialize Socket.IO connection
        this.socket = io({
            transports: ['websocket', 'polling'],
            timeout: 5000,
            forceNew: true
        });
        
        this.socket.on('connect', () => {
            console.log('🔗 Connected to live events server');
            this.reconnectAttempts = 0;
            this.showConnectionStatus('connected');
            
            // Rejoin previously subscribed events
            this.subscribedEvents.forEach(eventId => {
                this.joinEvent(eventId);
            });
        });
        
        this.socket.on('disconnect', () => {
            console.log('❌ Disconnected from live events server');
            this.showConnectionStatus('disconnected');
            this.attemptReconnect();
        });
        
        this.socket.on('live_update', (data) => {
            this.handleLiveUpdate(data);
        });
        
        this.socket.on('event_status', (data) => {
            this.updateEventStatus(data);
        });
        
        this.socket.on('notification', (data) => {
            this.showNotification(data);
        });
        
        this.socket.on('error', (error) => {
            console.error('Socket error:', error);
            this.showError('Connection error: ' + error.message);
        });
    }
    
    setupEventHandlers() {
        // Auto-refresh button
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('join-event-btn')) {
                const eventId = e.target.dataset.eventId;
                this.subscribeToEvent(eventId);
            }
            
            if (e.target.classList.contains('leave-event-btn')) {
                const eventId = e.target.dataset.eventId;
                this.unsubscribeFromEvent(eventId);
            }
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'r') {
                e.preventDefault();
                this.refreshAllEvents();
            }
        });
        
        // Visibility change handling
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseUpdates();
            } else {
                this.resumeUpdates();
            }
        });
    }
    
    subscribeToEvent(eventId) {
        if (this.subscribedEvents.has(eventId)) {
            return; // Already subscribed
        }
        
        this.subscribedEvents.add(eventId);
        this.joinEvent(eventId);
        
        // Update UI
        this.updateSubscriptionButton(eventId, true);
        this.showToast('🔔 Subscribed to live updates', 'success');
    }
    
    unsubscribeFromEvent(eventId) {
        this.subscribedEvents.delete(eventId);
        
        this.socket.emit('leave_event', {
            event_id: parseInt(eventId),
            user_id: this.getCurrentUserId()
        });
        
        // Update UI
        this.updateSubscriptionButton(eventId, false);
        this.showToast('🔕 Unsubscribed from updates', 'info');
    }
    
    joinEvent(eventId) {
        this.socket.emit('join_event', {
            event_id: parseInt(eventId),
            user_id: this.getCurrentUserId()
        });
    }
    
    handleLiveUpdate(data) {
        const { event_id, update, timestamp, update_type, priority } = data;
        
        // Store update in history
        if (!this.updateHistory.has(event_id)) {
            this.updateHistory.set(event_id, []);
        }
        this.updateHistory.get(event_id).unshift({
            update,
            timestamp,
            update_type,
            priority
        });
        
        // Limit history size
        if (this.updateHistory.get(event_id).length > 50) {
            this.updateHistory.get(event_id).pop();
        }
        
        // Update UI
        this.displayUpdate(event_id, update, timestamp, update_type, priority);
        
        // Show notification for high priority updates
        if (priority === 'critical' || priority === 'high') {
            this.showPriorityNotification(event_id, update, priority);
        }
        
        // Play sound for critical updates
        if (priority === 'critical') {
            this.playNotificationSound();
        }
    }
    
    displayUpdate(eventId, update, timestamp, updateType, priority) {
        const eventCard = document.querySelector(`[data-event-id="${eventId}"]`);
        if (!eventCard) return;
        
        // Create update element
        const updateElement = this.createUpdateElement(update, timestamp, updateType, priority);
        
        // Add to updates container
        const updatesContainer = eventCard.querySelector('.live-updates');
        if (updatesContainer) {
            updatesContainer.insertBefore(updateElement, updatesContainer.firstChild);
            
            // Limit displayed updates
            const updates = updatesContainer.querySelectorAll('.update-item');
            if (updates.length > 10) {
                updates[updates.length - 1].remove();
            }
        }
        
        // Update last updated time
        const lastUpdatedElement = eventCard.querySelector('.last-updated');
        if (lastUpdatedElement) {
            lastUpdatedElement.textContent = `Last updated: ${this.formatTimestamp(timestamp)}`;
        }
        
        // Add visual indication
        this.highlightEventCard(eventId, priority);
    }
    
    createUpdateElement(update, timestamp, updateType, priority) {
        const div = document.createElement('div');
        div.className = `update-item priority-${priority} type-${updateType}`;
        
        const priorityIcon = this.getPriorityIcon(priority);
        const typeIcon = this.getTypeIcon(updateType);
        
        div.innerHTML = `
            <div class="update-header">
                <span class="update-icons">
                    ${priorityIcon}
                    ${typeIcon}
                </span>
                <span class="update-time">${this.formatTimestamp(timestamp)}</span>
            </div>
            <div class="update-content">${this.escapeHtml(update)}</div>
        `;
        
        // Add animation
        div.style.opacity = '0';
        div.style.transform = 'translateY(-10px)';
        
        requestAnimationFrame(() => {
            div.style.transition = 'all 0.3s ease';
            div.style.opacity = '1';
            div.style.transform = 'translateY(0)';
        });
        
        return div;
    }
    
    highlightEventCard(eventId, priority) {
        const eventCard = document.querySelector(`[data-event-id="${eventId}"]`);
        if (!eventCard) return;
        
        const highlightClass = `highlight-${priority}`;
        eventCard.classList.add(highlightClass);
        
        // Remove highlight after animation
        setTimeout(() => {
            eventCard.classList.remove(highlightClass);
        }, 2000);
    }
    
    showPriorityNotification(eventId, update, priority) {
        // Browser notification (if permission granted)
        if (Notification.permission === 'granted') {
            const notification = new Notification('🔴 Live Event Update', {
                body: update.substring(0, 100) + (update.length > 100 ? '...' : ''),
                icon: '/static/icon-192.png',
                badge: '/static/icon-192.png',
                tag: `event-${eventId}`,
                requireInteraction: priority === 'critical'
            });
            
            notification.onclick = () => {
                window.focus();
                this.scrollToEvent(eventId);
                notification.close();
            };
            
            // Auto-close after delay
            setTimeout(() => notification.close(), 5000);
        }
        
        // In-page notification
        this.showToast(`🚨 ${update}`, priority === 'critical' ? 'error' : 'warning');
    }
    
    playNotificationSound() {
        // Create and play notification sound
        const audio = new Audio('/static/sounds/notification.mp3');
        audio.volume = 0.3;
        audio.play().catch(e => console.log('Audio play failed:', e));
    }
    
    showConnectionStatus(status) {
        const statusElement = document.querySelector('.connection-status');
        if (statusElement) {
            statusElement.className = `connection-status ${status}`;
            statusElement.textContent = status === 'connected' ? '🟢 Live' : '🔴 Disconnected';
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.pow(2, this.reconnectAttempts) * 1000; // Exponential backoff
            
            setTimeout(() => {
                console.log(`🔄 Reconnection attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
                this.socket.connect();
            }, delay);
        } else {
            this.showError('Unable to reconnect. Please refresh the page.');
        }
    }
    
    refreshAllEvents() {
        this.subscribedEvents.forEach(eventId => {
            this.socket.emit('request_event_status', { event_id: parseInt(eventId) });
        });
        
        this.showToast('🔄 Refreshing all events...', 'info');
    }
    
    pauseUpdates() {
        // Implement pause logic if needed
        console.log('🛑 Updates paused (page hidden)');
    }
    
    resumeUpdates() {
        // Implement resume logic if needed
        console.log('▶️ Updates resumed (page visible)');
    }
    
    getCurrentUserId() {
        // Get current user ID from session or page data
        return window.currentUserId || document.body.dataset.userId || 1;
    }
    
    getPriorityIcon(priority) {
        const icons = {
            'critical': '🔴',
            'high': '🟠',
            'normal': '🟡',
            'low': '⚪'
        };
        return icons[priority] || icons.normal;
    }
    
    getTypeIcon(type) {
        const icons = {
            'goal': '⚽',
            'penalty': '🥅',
            'red_card': '🟥',
            'yellow_card': '🟨',
            'substitution': '🔄',
            'market_update': '📈',
            'announcement': '📢',
            'breaking_news': '🚨'
        };
        return icons[type] || '📝';
    }
    
    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString();
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    scrollToEvent(eventId) {
        const eventCard = document.querySelector(`[data-event-id="${eventId}"]`);
        if (eventCard) {
            eventCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
    
    updateSubscriptionButton(eventId, isSubscribed) {
        const button = document.querySelector(`[data-event-id="${eventId}"] .subscription-btn`);
        if (button) {
            button.textContent = isSubscribed ? '🔕 Unsubscribe' : '🔔 Subscribe';
            button.className = `btn ${isSubscribed ? 'btn-secondary leave-event-btn' : 'btn-primary join-event-btn'}`;
        }
    }
    
    showToast(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        // Add to page
        const container = document.querySelector('.toast-container') || document.body;
        container.appendChild(toast);
        
        // Animate in
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });
        
        // Remove after delay
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
    
    showError(message) {
        this.showToast(`❌ ${message}`, 'error');
    }
    
    // Request notification permission
    static async requestNotificationPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            const permission = await Notification.requestPermission();
            return permission === 'granted';
        }
        return Notification.permission === 'granted';
    }
}

// Enhanced CSS for live events
const ENHANCED_LIVE_EVENTS_CSS = `
.live-events-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

.connection-status {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 8px 16px;
    border-radius: 20px;
    font-weight: bold;
    z-index: 1000;
    transition: all 0.3s ease;
}

.connection-status.connected {
    background: #4CAF50;
    color: white;
}

.connection-status.disconnected {
    background: #f44336;
    color: white;
    animation: pulse 1s infinite;
}

.event-card {
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    margin-bottom: 20px;
    padding: 20px;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

.event-card.highlight-critical {
    animation: criticalPulse 2s ease-in-out;
    border-left: 5px solid #f44336;
}

.event-card.highlight-high {
    animation: highPulse 2s ease-in-out;
    border-left: 5px solid #ff9800;
}

.event-card.highlight-normal {
    animation: normalPulse 1s ease-in-out;
    border-left: 5px solid #2196F3;
}

@keyframes criticalPulse {
    0%, 100% { background: white; }
    50% { background: #ffebee; }
}

@keyframes highPulse {
    0%, 100% { background: white; }
    50% { background: #fff3e0; }
}

@keyframes normalPulse {
    0%, 100% { background: white; }
    50% { background: #e3f2fd; }
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}

.live-updates {
    max-height: 400px;
    overflow-y: auto;
    margin-top: 15px;
}

.update-item {
    padding: 12px;
    margin-bottom: 8px;
    border-radius: 8px;
    border-left: 4px solid #ddd;
    background: #f9f9f9;
    transition: all 0.3s ease;
}

.update-item.priority-critical {
    border-left-color: #f44336;
    background: #ffebee;
}

.update-item.priority-high {
    border-left-color: #ff9800;
    background: #fff3e0;
}

.update-item.priority-normal {
    border-left-color: #2196F3;
    background: #e3f2fd;
}

.update-item.priority-low {
    border-left-color: #9e9e9e;
    background: #f5f5f5;
}

.update-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    font-size: 0.9em;
    color: #666;
}

.update-icons {
    display: flex;
    gap: 5px;
}

.update-content {
    font-size: 1em;
    line-height: 1.4;
    color: #333;
}

.toast-container {
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 2000;
}

.toast {
    padding: 12px 20px;
    border-radius: 6px;
    margin-bottom: 10px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    opacity: 0;
    transform: translateY(-20px);
    transition: all 0.3s ease;
    max-width: 400px;
    text-align: center;
    font-weight: 500;
}

.toast.show {
    opacity: 1;
    transform: translateY(0);
}

.toast.toast-success {
    background: #4CAF50;
    color: white;
}

.toast.toast-error {
    background: #f44336;
    color: white;
}

.toast.toast-warning {
    background: #ff9800;
    color: white;
}

.toast.toast-info {
    background: #2196F3;
    color: white;
}

.subscription-btn {
    transition: all 0.3s ease;
}

.subscription-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}

.last-updated {
    font-size: 0.8em;
    color: #666;
    font-style: italic;
}

.event-stats {
    display: flex;
    gap: 15px;
    margin-top: 10px;
    font-size: 0.9em;
}

.stat-item {
    display: flex;
    align-items: center;
    gap: 5px;
    color: #666;
}

.live-indicator {
    display: inline-block;
    width: 10px;
    height: 10px;
    background: #4CAF50;
    border-radius: 50%;
    animation: pulse 2s infinite;
}

.performance-metrics {
    position: fixed;
    bottom: 20px;
    left: 20px;
    background: rgba(0,0,0,0.8);
    color: white;
    padding: 10px;
    border-radius: 6px;
    font-size: 0.8em;
    z-index: 1000;
}

@media (max-width: 768px) {
    .live-events-container {
        padding: 10px;
    }
    
    .event-card {
        padding: 15px;
    }
    
    .connection-status {
        top: 10px;
        right: 10px;
        font-size: 0.9em;
    }
    
    .update-item {
        padding: 10px;
    }
}
`;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Add CSS to page
    const style = document.createElement('style');
    style.textContent = ENHANCED_LIVE_EVENTS_CSS;
    document.head.appendChild(style);
    
    // Create toast container
    const toastContainer = document.createElement('div');
    toastContainer.className = 'toast-container';
    document.body.appendChild(toastContainer);
    
    // Initialize live events manager
    window.liveEventsManager = new LiveEventsManager();
    
    // Request notification permission
    LiveEventsManager.requestNotificationPermission();
});
"""
