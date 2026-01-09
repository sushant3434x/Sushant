const cacheName='neet720-v1';
const filesToCache=['/','/index.html','/manifest.json','/icon192.png','/icon512.png','https://cdn.jsdelivr.net/npm/chart.js'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(cacheName).then(cache=>cache.addAll(filesToCache)))});
self.addEventListener('fetch',e=>{e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request)))});

