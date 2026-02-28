const CACHE_NAME = 'ridebuddy-cache-v2';
const ASSETS_TO_CACHE = [
    '/',
    '/static/style.css',
    '/static/script.js'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS_TO_CACHE))
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
            );
        })
    );
});

self.addEventListener('fetch', (event) => {
    event.respondWith(
        fetch(event.request).catch(() => caches.match(event.request))
    );
});

self.addEventListener('push', (event) => {
    const options = {
        body: 'A student is waiting for you!',
        icon: '/static/assets/media/icon-192.png',
        badge: '/static/assets/media/icon-192.png',
        vibrate: [100, 50, 100]
    };
    event.waitUntil(self.registration.showNotification('RideBuddy Notification', options));
});
