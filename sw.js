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
      Promise.all(keys.filter(k => k !== CACHE && k !== 'solar-notif-v1').map(k => caches.delete(k)))
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

// ── Periodic Background Sync ──────────────────────────────────────────────────
// Fires every ~15 min even when the app is closed (requires PWA install + Chrome).
// Reads the notification payload cached by the page (storeNotifPayloads) and posts
// morning / evening notifications at the correct time windows.
self.addEventListener('periodicsync', e => {
  if (e.tag === 'solar-refresh') {
    e.waitUntil(handlePeriodicSync());
  }
});

async function handlePeriodicSync() {
  const now = new Date();
  const h   = now.getHours() + now.getMinutes() / 60;
  const todayKey = now.toDateString();

  // If the page is visible, let it handle everything — just wake it up
  const allClients = await clients.matchAll({ type: 'window', includeUncontrolled: true });
  const pageVisible = allClients.some(c => c.visibilityState === 'visible');
  if (pageVisible) {
    allClients.forEach(c => c.postMessage({ type: 'BACKGROUND_SYNC' }));
    return;
  }

  // Page is backgrounded or closed — read cached notification payload
  let payload = null;
  try {
    const notifCache = await caches.open('solar-notif-v1');
    const r = await notifCache.match('/solar-notif-payload');
    if (r) payload = await r.json();
  } catch(e) {}

  if (!payload || payload.date !== todayKey) return;

  // Morning notification window: 07:30 – 10:00
  if (h >= 7.5 && h < 10 && payload.morning) {
    const existing = await self.registration.getNotifications({ tag: 'morning-forecast-' + todayKey });
    if (existing.length === 0) {
      await self.registration.showNotification(payload.morning.title, {
        body: payload.morning.body,
        tag:  'morning-forecast-' + todayKey,
        icon: '/icons/icon-192.png',
        badge: '/icons/icon-72.png',
        vibrate: [200, 100, 200],
        data: { url: '/' },
        actions: [{ action: 'open', title: 'Open dashboard' }],
      });
    }
  }

  // Evening notification window: 20:00 – 22:00
  if (h >= 20 && h < 22 && payload.evening) {
    const existing = await self.registration.getNotifications({ tag: 'evening-forecast-' + todayKey });
    if (existing.length === 0) {
      await self.registration.showNotification(payload.evening.title, {
        body: payload.evening.body,
        tag:  'evening-forecast-' + todayKey,
        icon: '/icons/icon-192.png',
        badge: '/icons/icon-72.png',
        vibrate: [200, 100, 200],
        data: { url: '/' },
        actions: [{ action: 'open', title: 'Open dashboard' }],
      });
    }
  }

  // Wake up any backgrounded (not visible) page clients so they can refresh
  allClients.forEach(c => c.postMessage({ type: 'BACKGROUND_SYNC' }));
}

// Handle notification clicks — open the dashboard
self.addEventListener('notificationclick', e => {
  e.notification.close();
  if (e.action === 'open' || !e.action) {
    e.waitUntil(
      clients.matchAll({ type: 'window', includeUncontrolled: true }).then(wins => {
        for (const win of wins) {
          if (win.url.includes(self.location.origin) && 'focus' in win) {
            return win.focus();
          }
        }
        if (clients.openWindow) return clients.openWindow('/');
      })
    );
  }
});

self.addEventListener('message', e => {
  if (e.data && e.data.type === 'SKIP_WAITING') self.skipWaiting();
});
