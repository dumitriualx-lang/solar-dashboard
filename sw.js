// Solar Dashboard — Service Worker
// Caches all assets on first load → full offline support

const CACHE = 'solar-dashboard-v3';
const ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  '/icons/icon-any-192.png',
  '/icons/icon-any-512.png',
  '/icons/icon-any-1024.png',
  '/screenshots/screenshot-dashboard.png',
  '/screenshots/screenshot-forecast.png',
  '/screenshots/screenshot-schedule.png',
  'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js',
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(cache => cache.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    caches.match(e.request).then(cached => {
      if (cached) return cached;
      return fetch(e.request).then(response => {
        if (response && response.status === 200 && response.type !== 'opaque') {
          const clone = response.clone();
          caches.open(CACHE).then(cache => cache.put(e.request, clone));
        }
        return response;
      }).catch(() => {
        if (e.request.mode === 'navigate') return caches.match('/index.html');
      });
    })
  );
});

// Handle notification clicks — open the dashboard
self.addEventListener('notificationclick', e => {
  e.notification.close();
  if (e.action === 'open' || !e.action) {
    e.waitUntil(
      clients.matchAll({ type: 'window', includeUncontrolled: true }).then(wins => {
        // Focus existing window if open
        for (const win of wins) {
          if (win.url.includes(self.location.origin) && 'focus' in win) {
            return win.focus();
          }
        }
        // Otherwise open new window
        if (clients.openWindow) return clients.openWindow('/');
      })
    );
  }
});

self.addEventListener('message', e => {
  if (e.data && e.data.type === 'SKIP_WAITING') self.skipWaiting();
});
