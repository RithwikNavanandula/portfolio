/**
 * Service Worker for Label Scanner
 * Caches app assets for offline use
 */

const CACHE_NAME = 'label-scanner-v2';
const ASSETS_TO_CACHE = [
    './',
    './index.html',
    './css/styles.css',
    './js/storage.js',
    './js/parser.js',
    './js/ocr.js',
    './js/offline-ocr.js',
    './js/app.js'
];

// External resources to cache
const EXTERNAL_CACHE = [
    'https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js'
];

// Install event - cache assets
self.addEventListener('install', event => {
    console.log('[SW] Installing...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('[SW] Caching app assets');
                return Promise.all([
                    cache.addAll(ASSETS_TO_CACHE),
                    // Cache external resources separately (may fail)
                    ...EXTERNAL_CACHE.map(url =>
                        cache.add(url).catch(err => console.log('[SW] Failed to cache:', url))
                    )
                ]);
            })
            .then(() => self.skipWaiting())
    );
});

// Activate event - clean old caches
self.addEventListener('activate', event => {
    console.log('[SW] Activating...');
    event.waitUntil(
        caches.keys()
            .then(names => {
                return Promise.all(
                    names.map(name => {
                        if (name !== CACHE_NAME) {
                            console.log('[SW] Deleting old cache:', name);
                            return caches.delete(name);
                        }
                    })
                );
            })
            .then(() => self.clients.claim())
    );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);

    // Skip non-GET requests
    if (event.request.method !== 'GET') return;

    // Skip API requests (OCR.space)
    if (url.hostname === 'api.ocr.space') return;

    // Skip Google Sheets requests
    if (url.hostname.includes('googleapis.com') || url.hostname.includes('google.com')) return;

    event.respondWith(
        caches.match(event.request)
            .then(cached => {
                if (cached) {
                    console.log('[SW] Serving from cache:', event.request.url);
                    return cached;
                }

                // Fetch from network
                return fetch(event.request)
                    .then(response => {
                        // Don't cache non-ok responses
                        if (!response || response.status !== 200) {
                            return response;
                        }

                        // Cache the new resource
                        const clone = response.clone();
                        caches.open(CACHE_NAME)
                            .then(cache => cache.put(event.request, clone));

                        return response;
                    })
                    .catch(err => {
                        console.log('[SW] Fetch failed:', err);
                        // Return a fallback for HTML pages
                        if (event.request.headers.get('accept').includes('text/html')) {
                            return caches.match('/index.html');
                        }
                    });
            })
    );
});
