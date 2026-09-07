/* Solo existe para que la app se pueda instalar.
   No cachea nada: asi cualquier cambio publicado llega enseguida. */
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', ev => ev.waitUntil(self.clients.claim()));
self.addEventListener('fetch', () => {});
