/* BFRB Detection — Service Worker (Tier 4 / 4.6)
 * -----------------------------------------------
 * Caches the app shell so the PWA loads instantly and works offline for
 * non-network features (HUD/history, manual review). Live detection still
 * needs the camera + the Flask backend at runtime.
 *
 * Strategy:
 *   - cache-first for the shell + static assets + MediaPipe CDN scripts
 *   - network-first for /api/* (always try fresh data, fall back to cache)
 */

const CACHE_VERSION = "bfrb-v5-2026-05-06";
const SHELL_ASSETS = [
  "/",
  "/static/manifest.json",
  "/static/icon-192.png",
  "/static/icon-512.png",
  // CDN deps that the app needs to render
  "https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js",
  "https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js",
  "https://cdn.jsdelivr.net/npm/@mediapipe/holistic/holistic.js",
  "https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js",
  "https://cdn.socket.io/4.7.5/socket.io.min.js",
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then(cache => cache.addAll(SHELL_ASSETS).catch(() => {}))
  );
  self.skipWaiting();
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.map(k => (k === CACHE_VERSION ? null : caches.delete(k))))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", event => {
  const req = event.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);

  // network-first for live API data
  if (url.pathname.startsWith("/api/")) {
    event.respondWith(
      fetch(req)
        .then(res => {
          const copy = res.clone();
          caches.open(CACHE_VERSION).then(c => c.put(req, copy)).catch(() => {});
          return res;
        })
        .catch(() => caches.match(req))
    );
    return;
  }

  // cache-first for the shell + CDN assets
  event.respondWith(
    caches.match(req).then(hit => {
      if (hit) return hit;
      return fetch(req).then(res => {
        if (!res || res.status !== 200) return res;
        const copy = res.clone();
        caches.open(CACHE_VERSION).then(c => c.put(req, copy)).catch(() => {});
        return res;
      });
    })
  );
});
