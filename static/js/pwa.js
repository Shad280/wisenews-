// PWA Installation and offline functionality
let deferredPrompt;
let isOnline = navigator.onLine;

// Register Service Worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/sw.js')
      .then(registration => {
        console.log('SW registered: ', registration);
        
        // Check for updates
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              showUpdateAvailable();
            }
          });
        });
      })
      .catch(registrationError => {
        console.log('SW registration failed: ', registrationError);
      });
  });
}

// PWA Install prompt
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  showInstallButton();
});

function showInstallButton() {
  const installBtn = document.getElementById('install-btn');
  if (installBtn) {
    installBtn.style.display = 'block';
    installBtn.addEventListener('click', installApp);
  }
}

function installApp() {
  const installBtn = document.getElementById('install-btn');
  if (deferredPrompt) {
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then((choiceResult) => {
      if (choiceResult.outcome === 'accepted') {
        console.log('User accepted the install prompt');
        installBtn.style.display = 'none';
      }
      deferredPrompt = null;
    });
  }
}

// Online/Offline status
window.addEventListener('online', () => {
  isOnline = true;
  showOnlineStatus();
  syncOfflineData();
});

window.addEventListener('offline', () => {
  isOnline = false;
  showOfflineStatus();
});

function showOnlineStatus() {
  const statusBar = document.getElementById('connection-status');
  if (statusBar) {
    statusBar.textContent = 'Online';
    statusBar.className = 'status-online';
  }
}

function showOfflineStatus() {
  const statusBar = document.getElementById('connection-status');
  if (statusBar) {
    statusBar.textContent = 'Offline - Using cached content';
    statusBar.className = 'status-offline';
  }
}

function showUpdateAvailable() {
  const updateBar = document.getElementById('update-bar');
  if (updateBar) {
    updateBar.style.display = 'block';
    updateBar.innerHTML = `
      <span>New version available!</span>
      <button onclick="updateApp()">Update Now</button>
    `;
  }
}

function updateApp() {
  window.location.reload();
}

function syncOfflineData() {
  if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
    navigator.serviceWorker.ready.then(registration => {
      return registration.sync.register('background-sync');
    });
  }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  // Show initial connection status
  if (isOnline) {
    showOnlineStatus();
  } else {
    showOfflineStatus();
  }
});

// Add mobile-friendly touch events
document.addEventListener('touchstart', handleTouchStart, false);
document.addEventListener('touchmove', handleTouchMove, false);

let xDown = null;
let yDown = null;

function getTouches(evt) {
  return evt.touches || evt.originalEvent.touches;
}

function handleTouchStart(evt) {
  const firstTouch = getTouches(evt)[0];
  xDown = firstTouch.clientX;
  yDown = firstTouch.clientY;
}

function handleTouchMove(evt) {
  if (!xDown || !yDown) {
    return;
  }

  const xUp = evt.touches[0].clientX;
  const yUp = evt.touches[0].clientY;

  const xDiff = xDown - xUp;
  const yDiff = yDown - yUp;

  if (Math.abs(xDiff) > Math.abs(yDiff)) {
    if (xDiff > 0) {
      // Left swipe
      console.log('Swiped left');
    } else {
      // Right swipe
      console.log('Swiped right');
    }
  }

  xDown = null;
  yDown = null;
}
