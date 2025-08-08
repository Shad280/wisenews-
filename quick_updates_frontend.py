"""
Real-Time Frontend Components for Quick Updates
Ultra-fast UI updates with optimized WebSocket handling
"""

QUICK_UPDATES_FRONTEND = """
<!-- Quick Updates Real-Time Interface -->
<div id="quick-updates-container" style="position: fixed; top: 20px; right: 20px; z-index: 9999;">
    <div id="update-notifications" class="update-notifications"></div>
    <div id="performance-indicator" class="performance-indicator">
        <div class="indicator-dot" id="connection-status"></div>
        <span id="update-speed">0 ms</span>
    </div>
</div>

<style>
.update-notifications {
    max-width: 300px;
    margin-bottom: 10px;
}

.update-notification {
    background: rgba(0, 123, 255, 0.95);
    color: white;
    padding: 10px 15px;
    margin-bottom: 5px;
    border-radius: 5px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    animation: slideInRight 0.3s ease-out;
    position: relative;
    overflow: hidden;
}

.update-notification.priority-high {
    background: rgba(220, 53, 69, 0.95);
    animation: pulse 1s infinite;
}

.update-notification.priority-medium {
    background: rgba(255, 193, 7, 0.95);
}

.update-notification.success {
    background: rgba(40, 167, 69, 0.95);
}

.performance-indicator {
    display: flex;
    align-items: center;
    background: rgba(33, 37, 41, 0.9);
    color: white;
    padding: 5px 10px;
    border-radius: 15px;
    font-size: 12px;
    backdrop-filter: blur(5px);
}

.indicator-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 8px;
    animation: pulse 2s infinite;
}

.indicator-dot.connected {
    background: #28a745;
}

.indicator-dot.connecting {
    background: #ffc107;
}

.indicator-dot.disconnected {
    background: #dc3545;
}

@keyframes slideInRight {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.7; }
    100% { opacity: 1; }
}

@keyframes fadeOut {
    from { opacity: 1; transform: translateX(0); }
    to { opacity: 0; transform: translateX(100%); }
}

.update-notification.fade-out {
    animation: fadeOut 0.3s ease-in forwards;
}

/* Mobile optimizations */
@media (max-width: 768px) {
    #quick-updates-container {
        top: 10px;
        right: 10px;
        left: 10px;
    }
    
    .update-notifications {
        max-width: none;
    }
    
    .update-notification {
        font-size: 14px;
        padding: 8px 12px;
    }
}
</style>

<script>
class QuickUpdatesClient {
    constructor() {
        this.socket = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.performanceMetrics = {
            totalUpdates: 0,
            avgResponseTime: 0,
            lastUpdateTime: null
        };
        
        this.notificationContainer = document.getElementById('update-notifications');
        this.connectionStatus = document.getElementById('connection-status');
        this.updateSpeedIndicator = document.getElementById('update-speed');
        
        this.init();
    }
    
    init() {
        this.connect();
        this.setupPerformanceMonitoring();
    }
    
    connect() {
        try {
            // Initialize Socket.IO connection
            this.socket = io({
                transports: ['websocket', 'polling'],
                upgrade: true,
                timeout: 5000,
                forceNew: false
            });
            
            this.socket.on('connect', () => {
                this.connected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus('connected');
                console.log('✅ Quick Updates: Connected to real-time server');
                
                // Subscribe to quick updates
                this.socket.emit('join_room', { room: 'quick_updates' });
                
                this.showNotification('Connected to real-time updates', 'success');
            });
            
            this.socket.on('disconnect', () => {
                this.connected = false;
                this.updateConnectionStatus('disconnected');
                console.log('❌ Quick Updates: Disconnected from server');
                this.attemptReconnect();
            });
            
            this.socket.on('connect_error', (error) => {
                console.error('Connection error:', error);
                this.updateConnectionStatus('disconnected');
                this.attemptReconnect();
            });
            
            // Handle quick updates
            this.socket.on('quick_update', (data) => {
                this.handleQuickUpdate(data);
            });
            
            // Handle specific update types
            this.socket.on('new_article_update', (data) => {
                this.handleNewArticle(data);
            });
            
            this.socket.on('live_event_update', (data) => {
                this.handleLiveEventUpdate(data);
            });
            
            this.socket.on('article_update', (data) => {
                this.handleArticleUpdate(data);
            });
            
        } catch (error) {
            console.error('Failed to initialize socket connection:', error);
            this.updateConnectionStatus('disconnected');
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            this.updateConnectionStatus('connecting');
            
            setTimeout(() => {
                console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                this.connect();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.error('Max reconnection attempts reached');
            this.showNotification('Connection lost. Please refresh the page.', 'error', 10000);
        }
    }
    
    handleQuickUpdate(data) {
        const startTime = performance.now();
        
        try {
            const updateType = data.type;
            const updateData = data.data;
            
            // Update performance metrics
            this.performanceMetrics.totalUpdates++;
            this.performanceMetrics.lastUpdateTime = new Date();
            
            // Handle different update types
            switch (updateType) {
                case 'new_article':
                    this.processNewArticle(updateData);
                    break;
                case 'article_update':
                    this.processArticleUpdate(updateData);
                    break;
                case 'live_event_update':
                    this.processLiveEventUpdate(updateData);
                    break;
                case 'cache_invalidation':
                    this.processCacheInvalidation(updateData);
                    break;
                default:
                    console.log('Unknown update type:', updateType);
            }
            
            // Calculate and display response time
            const responseTime = performance.now() - startTime;
            this.updatePerformanceIndicator(responseTime);
            
        } catch (error) {
            console.error('Error handling quick update:', error);
        }
    }
    
    processNewArticle(articleData) {
        // Add new article to the page if we're on articles list
        if (window.location.pathname.includes('/articles')) {
            this.addArticleToList(articleData);
        }
        
        // Show notification
        this.showNotification(
            `New article: ${articleData.title.substring(0, 50)}...`,
            'info',
            5000
        );
        
        // Update counters
        this.updateArticleCounters(1);
    }
    
    processArticleUpdate(articleData) {
        // Update existing article if visible
        const articleElement = document.querySelector(`[data-article-id="${articleData.id}"]`);
        if (articleElement) {
            this.updateArticleElement(articleElement, articleData);
        }
    }
    
    processLiveEventUpdate(eventData) {
        // High priority notification for live events
        this.showNotification(
            `🔴 Live: ${eventData.title || 'Event Update'}`,
            'priority-high',
            8000
        );
        
        // Update live events section if visible
        this.updateLiveEventsSection(eventData);
    }
    
    processCacheInvalidation(data) {
        // Clear local caches if we have any
        if (typeof window.articleCache !== 'undefined') {
            window.articleCache.clear();
        }
        
        // Refresh current page data if needed
        if (data.refreshPage) {
            this.refreshCurrentPageData();
        }
    }
    
    addArticleToList(articleData) {
        const articlesList = document.querySelector('.articles-list, .article-grid');
        if (articlesList) {
            const articleHtml = this.createArticleHTML(articleData);
            articlesList.insertAdjacentHTML('afterbegin', articleHtml);
            
            // Animate the new article
            const newArticle = articlesList.firstElementChild;
            newArticle.style.opacity = '0';
            newArticle.style.transform = 'translateY(-20px)';
            
            requestAnimationFrame(() => {
                newArticle.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                newArticle.style.opacity = '1';
                newArticle.style.transform = 'translateY(0)';
            });
        }
    }
    
    createArticleHTML(articleData) {
        return `
            <div class="article-item" data-article-id="${articleData.id}">
                <div class="article-header">
                    <h3><a href="/article/${articleData.id}">${this.escapeHtml(articleData.title)}</a></h3>
                    <span class="article-meta">
                        ${articleData.source_name} • ${this.formatDate(articleData.date_added)}
                    </span>
                </div>
                <div class="article-preview">
                    ${this.escapeHtml(articleData.content.substring(0, 200))}...
                </div>
                <div class="article-tags">
                    <span class="tag">${articleData.category}</span>
                    <span class="tag source">${articleData.source_type}</span>
                </div>
            </div>
        `;
    }
    
    updateArticleElement(element, articleData) {
        // Update title if changed
        const titleElement = element.querySelector('h3 a');
        if (titleElement && articleData.title) {
            titleElement.textContent = articleData.title;
        }
        
        // Update read status
        if ('read_status' in articleData) {
            element.classList.toggle('read', articleData.read_status);
        }
        
        // Add update indicator
        element.classList.add('updated');
        setTimeout(() => {
            element.classList.remove('updated');
        }, 2000);
    }
    
    updateLiveEventsSection(eventData) {
        const liveEventsContainer = document.querySelector('#live-events-container');
        if (liveEventsContainer) {
            // Update or add event
            const eventElement = document.querySelector(`[data-event-id="${eventData.event_id}"]`);
            if (eventElement) {
                this.updateEventElement(eventElement, eventData);
            } else {
                this.addNewEventElement(liveEventsContainer, eventData);
            }
        }
    }
    
    showNotification(message, type = 'info', duration = 5000) {
        if (!this.notificationContainer) return;
        
        const notification = document.createElement('div');
        notification.className = `update-notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">${this.escapeHtml(message)}</div>
            <div class="notification-time">${new Date().toLocaleTimeString()}</div>
        `;
        
        this.notificationContainer.appendChild(notification);
        
        // Auto-remove after duration
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, duration);
        
        // Limit number of notifications
        const notifications = this.notificationContainer.children;
        while (notifications.length > 5) {
            notifications[0].remove();
        }
    }
    
    updateConnectionStatus(status) {
        if (!this.connectionStatus) return;
        
        this.connectionStatus.className = `indicator-dot ${status}`;
        
        const statusText = {
            'connected': 'Connected',
            'connecting': 'Connecting...',
            'disconnected': 'Disconnected'
        };
        
        this.connectionStatus.title = statusText[status] || 'Unknown';
    }
    
    updatePerformanceIndicator(responseTime) {
        if (!this.updateSpeedIndicator) return;
        
        // Update average response time
        const totalUpdates = this.performanceMetrics.totalUpdates;
        const currentAvg = this.performanceMetrics.avgResponseTime;
        this.performanceMetrics.avgResponseTime = 
            (currentAvg * (totalUpdates - 1) + responseTime) / totalUpdates;
        
        // Display current response time
        this.updateSpeedIndicator.textContent = `${Math.round(responseTime)} ms`;
        
        // Color code based on performance
        const indicator = this.updateSpeedIndicator.parentElement;
        indicator.classList.remove('fast', 'medium', 'slow');
        
        if (responseTime < 50) {
            indicator.classList.add('fast');
        } else if (responseTime < 200) {
            indicator.classList.add('medium');
        } else {
            indicator.classList.add('slow');
        }
    }
    
    setupPerformanceMonitoring() {
        // Monitor performance every 30 seconds
        setInterval(() => {
            if (this.connected && this.socket) {
                this.socket.emit('request_performance_metrics');
            }
        }, 30000);
        
        // Handle performance metrics response
        if (this.socket) {
            this.socket.on('performance_metrics', (metrics) => {
                console.log('Performance metrics:', metrics);
                this.displayPerformanceMetrics(metrics);
            });
        }
    }
    
    displayPerformanceMetrics(metrics) {
        // Update performance indicator with server metrics
        if (this.updateSpeedIndicator) {
            const avgTime = metrics.avg_update_time_ms || 0;
            this.updateSpeedIndicator.title = 
                `Avg: ${avgTime}ms | Cache: ${metrics.cache_hit_rate_percent}% | Total: ${metrics.total_updates}`;
        }
    }
    
    // Utility methods
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString();
    }
    
    updateArticleCounters(increment) {
        const counters = document.querySelectorAll('.article-count, .total-articles');
        counters.forEach(counter => {
            const currentCount = parseInt(counter.textContent) || 0;
            counter.textContent = currentCount + increment;
        });
    }
    
    refreshCurrentPageData() {
        // Refresh page data without full reload
        if (typeof window.refreshPageData === 'function') {
            window.refreshPageData();
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if we have the required elements
    if (document.getElementById('quick-updates-container')) {
        window.quickUpdatesClient = new QuickUpdatesClient();
        console.log('✅ Quick Updates Client initialized');
    }
});

// Add performance indicator styles
const perfStyles = `
.performance-indicator.fast {
    background: rgba(40, 167, 69, 0.9);
}

.performance-indicator.medium {
    background: rgba(255, 193, 7, 0.9);
}

.performance-indicator.slow {
    background: rgba(220, 53, 69, 0.9);
}

.article-item.updated {
    border-left: 3px solid #007bff;
    background: rgba(0, 123, 255, 0.05);
    transition: all 0.3s ease;
}
`;

const styleSheet = document.createElement('style');
styleSheet.textContent = perfStyles;
document.head.appendChild(styleSheet);
</script>
"""

def inject_quick_updates_frontend():
    """Return the quick updates frontend code for injection into templates"""
    return QUICK_UPDATES_FRONTEND
