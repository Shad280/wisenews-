// Service Worker for WiseNews Push Notifications and PWA functionality
const CACHE_NAME = 'wisenews-v1';
const urlsToCache = [
    '/',
    '/static/manifest.json',
    '/static/icon-192.png',
    '/static/icon-512.png'
];

// Install event - cache resources
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => cache.addAll(urlsToCache))
    );
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                // Return cached version or fetch from network
                return response || fetch(event.request);
            }
        )
    );
});

// Push event - handle incoming push notifications
self.addEventListener('push', (event) => {
    console.log('Push notification received:', event);
    
    let notificationData = {};
    
    if (event.data) {
        try {
            notificationData = event.data.json();
        } catch (e) {
            notificationData = {
                title: 'WiseNews',
                body: event.data.text() || 'New news available!',
                icon: '/static/icon-192.png',
                badge: '/static/icon-192.png'
            };
        }
    } else {
        notificationData = {
            title: 'WiseNews',
            body: 'New news available!',
            icon: '/static/icon-192.png',
            badge: '/static/icon-192.png'
        };
    }
    
    const notificationOptions = {
        body: notificationData.body,
        icon: notificationData.icon || '/static/icon-192.png',
        badge: notificationData.badge || '/static/icon-192.png',
        data: notificationData.data || {},
        actions: [
            {
                action: 'read',
                title: 'Read Now',
                icon: '/static/icon-192.png'
            },
            {
                action: 'dismiss',
                title: 'Dismiss'
            }
        ],
        requireInteraction: true,
        tag: notificationData.tag || 'news-update',
        renotify: true,
        silent: false,
        vibrate: [200, 100, 200]
    };
    
    event.waitUntil(
        self.registration.showNotification(
            notificationData.title || 'WiseNews',
            notificationOptions
        )
    );
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
    console.log('Notification clicked:', event);
    
    event.notification.close();
    
    const action = event.action;
    const notificationData = event.notification.data;
    
    if (action === 'read') {
        // Open the specific article if URL is provided
        const urlToOpen = notificationData.url || '/';
        
        event.waitUntil(
            clients.matchAll({
                type: 'window',
                includeUncontrolled: true
            }).then((clientList) => {
                // Check if app is already open
                for (let client of clientList) {
                    if (client.url.includes(urlToOpen) && 'focus' in client) {
                        return client.focus();
                    }
                }
                
                // Open new window/tab
                if (clients.openWindow) {
                    return clients.openWindow(urlToOpen);
                }
            })
        );
    } else if (action === 'dismiss') {
        // Just close the notification (already handled above)
        console.log('Notification dismissed');
    } else {
        // Default action - open the main app
        event.waitUntil(
            clients.matchAll({
                type: 'window',
                includeUncontrolled: true
            }).then((clientList) => {
                // Focus existing window or open new one
                for (let client of clientList) {
                    if (client.url.includes('/') && 'focus' in client) {
                        return client.focus();
                    }
                }
                
                if (clients.openWindow) {
                    return clients.openWindow('/');
                }
            })
        );
    }
});

// Background sync for when connectivity returns
self.addEventListener('sync', (event) => {
    if (event.tag === 'background-sync') {
        event.waitUntil(
            // Sync any pending data when back online
            fetch('/api/sync-notifications', { method: 'POST' })
                .then(response => {
                    console.log('Notifications synced successfully');
                })
                .catch(error => {
                    console.log('Sync failed:', error);
                })
        );
    }
});

// Message event - handle messages from main thread
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    
    // Take control of all pages
    return self.clients.claim();
});

// Handle periodic background sync (if supported)
self.addEventListener('periodicsync', (event) => {
    if (event.tag === 'news-update') {
        event.waitUntil(
            fetch('/api/check-notifications')
                .then(response => response.json())
                .then(data => {
                    if (data.hasNotifications) {
                        self.registration.showNotification('WiseNews', {
                            body: 'New articles matching your interests are available!',
                            icon: '/static/icon-192.png',
                            badge: '/static/icon-192.png',
                            tag: 'periodic-update'
                        });
                    }
                })
                .catch(error => {
                    console.log('Periodic sync failed:', error);
                })
        );
    }
});

// Error handling
self.addEventListener('error', (event) => {
    console.error('Service Worker error:', event.error);
});

self.addEventListener('unhandledrejection', (event) => {
    console.error('Service Worker unhandled rejection:', event.reason);
});
