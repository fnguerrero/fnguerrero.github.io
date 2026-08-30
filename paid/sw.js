/* Service worker propio (sin librerías).
   - Navegación: red primero, con el index cacheado como respaldo offline.
   - Assets del build (JS/CSS/iconos): cache primero, y se van guardando a medida que se usan.
   Los nombres de los archivos del build llevan hash, así que el cache runtime alcanza:
   una versión nueva pide archivos nuevos y los viejos se limpian al activar. */

const VERSION = 'v3'
const CACHE_APP = `comprobantes-app-${VERSION}`
const CACHE_ASSETS = `comprobantes-assets-${VERSION}`

const BASE = new URL(self.registration.scope).pathname
const ESENCIALES = [BASE, `${BASE}index.html`, `${BASE}manifest.webmanifest`, `${BASE}icono-192.png`, `${BASE}icono-512.png`]

/* Al instalar NO se llama a skipWaiting: la version nueva queda esperando y la app avisa
   con el cartel "Hay una version nueva". Dos motivos:

   - Con skipWaiting el service worker nuevo toma el control de una pestana que ya cargo el
     JS viejo, y quedan mezcladas dos versiones de la misma app.
   - El cartel no llegaba a aparecer nunca, porque nunca habia un `waiting` que detectar,
     y su boton Actualizar le mandaba el mensaje a nadie.

   La espera se salta cuando el usuario toca Actualizar (ver el listener de 'message' de
   mas abajo), o sola cuando cierra todas las pestanas de la app. */
self.addEventListener('install', (evento) => {
  evento.waitUntil(
    caches
      .open(CACHE_APP)
      .then((cache) => cache.addAll(ESENCIALES.map((u) => new Request(u, { cache: 'reload' }))))
      .catch(() => {})
  )
})

self.addEventListener('activate', (evento) => {
  evento.waitUntil(
    caches
      .keys()
      .then((claves) =>
        Promise.all(claves.filter((c) => c !== CACHE_APP && c !== CACHE_ASSETS).map((c) => caches.delete(c)))
      )
      .then(() => self.clients.claim())
  )
})

self.addEventListener('fetch', (evento) => {
  const req = evento.request
  if (req.method !== 'GET') return

  const url = new URL(req.url)
  if (url.origin !== self.location.origin) return

  // Navegación: intento la red y, si no hay, devuelvo el index cacheado.
  if (req.mode === 'navigate') {
    evento.respondWith(
      fetch(req)
        .then((respuesta) => {
          const copia = respuesta.clone()
          caches.open(CACHE_APP).then((cache) => cache.put(`${BASE}index.html`, copia))
          return respuesta
        })
        .catch(() => caches.match(`${BASE}index.html`).then((r) => r || caches.match(BASE)))
    )
    return
  }

  // Assets: si está en cache lo sirvo directo; si no, lo bajo y lo guardo.
  evento.respondWith(
    caches.match(req).then((cacheado) => {
      if (cacheado) return cacheado
      return fetch(req)
        .then((respuesta) => {
          if (respuesta.ok && (respuesta.type === 'basic' || respuesta.type === 'default')) {
            const copia = respuesta.clone()
            caches.open(CACHE_ASSETS).then((cache) => cache.put(req, copia))
          }
          return respuesta
        })
        .catch(() => cacheado)
    })
  )
})

// Permite que la app fuerce la activación de una versión nueva.
self.addEventListener('message', (evento) => {
  if (evento.data === 'saltar-espera') self.skipWaiting()
})
