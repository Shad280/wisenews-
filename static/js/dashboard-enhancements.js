// Dashboard Enhancements
document.addEventListener('DOMContentLoaded', function() {
    // Animate cards on load
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'all 0.6s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });

    // Add hover effects to buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });

    // Animate progress bars
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(bar => {
        const width = bar.style.width;
        bar.style.width = '0%';
        setTimeout(() => {
            bar.style.width = width;
        }, 500);
    });

    // Add loading state to buttons on click
    const actionButtons = document.querySelectorAll('a.btn');
    actionButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (this.href && !this.href.includes('javascript:')) {
                this.classList.add('loading');
                this.style.pointerEvents = 'none';
                
                // Remove loading state after navigation
                setTimeout(() => {
                    this.classList.remove('loading');
                    this.style.pointerEvents = 'auto';
                }, 2000);
            }
        });
    });

    // Real-time usage updates (if socket.io is available)
    if (typeof io !== 'undefined') {
        const socket = io();
        
        socket.on('usage_update', function(data) {
            updateUsageMetrics(data);
        });
    }

    // Update usage metrics function
    function updateUsageMetrics(data) {
        if (data.articles_viewed !== undefined) {
            const articlesBadge = document.querySelector('.badge:contains("' + data.articles_viewed + '")');
            if (articlesBadge) {
                articlesBadge.textContent = data.articles_viewed + '/' + data.max_articles;
            }
        }
        
        if (data.searches_performed !== undefined) {
            const searchesBadge = document.querySelector('.badge:contains("' + data.searches_performed + '")');
            if (searchesBadge) {
                searchesBadge.textContent = data.searches_performed + '/' + data.max_searches;
            }
        }
    }

    // Smooth scroll for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Toast notifications
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} position-fixed top-0 end-0 m-3`;
        toast.style.zIndex = '9999';
        toast.style.minWidth = '300px';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }

    // Make showToast globally available
    window.showToast = showToast;

    // Check for flash messages and convert to toasts
    const flashMessages = document.querySelectorAll('.alert:not(.position-fixed)');
    flashMessages.forEach(alert => {
        const message = alert.textContent.trim();
        const type = alert.classList.contains('alert-success') ? 'success' : 
                    alert.classList.contains('alert-danger') ? 'danger' : 'info';
        
        // Remove original alert
        alert.style.display = 'none';
        
        // Show as toast
        setTimeout(() => showToast(message, type), 500);
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + / for search
        if ((e.ctrlKey || e.metaKey) && e.key === '/') {
            e.preventDefault();
            const searchInput = document.querySelector('input[name="q"]');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Ctrl/Cmd + D for dashboard
        if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
            e.preventDefault();
            window.location.href = '/';
        }
    });

    // Dynamic time updates
    function updateTimeElements() {
        const timeElements = document.querySelectorAll('[data-time]');
        timeElements.forEach(element => {
            const timestamp = element.getAttribute('data-time');
            if (timestamp) {
                element.textContent = formatTimeAgo(new Date(timestamp));
            }
        });
    }

    function formatTimeAgo(date) {
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);
        
        if (diffInSeconds < 60) return 'Just now';
        if (diffInSeconds < 3600) return Math.floor(diffInSeconds / 60) + ' minutes ago';
        if (diffInSeconds < 86400) return Math.floor(diffInSeconds / 3600) + ' hours ago';
        if (diffInSeconds < 604800) return Math.floor(diffInSeconds / 86400) + ' days ago';
        
        return date.toLocaleDateString();
    }

    // Update time elements every minute
    setInterval(updateTimeElements, 60000);
    updateTimeElements(); // Initial call

    // Performance monitoring
    if ('performance' in window) {
        window.addEventListener('load', function() {
            setTimeout(function() {
                const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
                console.log('Page load time:', loadTime + 'ms');
                
                if (loadTime > 3000) {
                    console.warn('Slow page load detected');
                }
            }, 0);
        });
    }

    // Service worker registration for PWA
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/sw.js')
            .then(registration => {
                console.log('SW registered:', registration);
            })
            .catch(error => {
                console.log('SW registration failed:', error);
            });
    }
});
