// ElectriApp Service Worker — notificaciones locales

self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));

// Recibe el mensaje para programar una notificación
self.addEventListener('message', e => {
  if (e.data && e.data.tipo === 'programar') {
    const { id, titulo, cuerpo, cuando } = e.data;
    const ahora = Date.now();
    const demora = cuando - ahora;

    if (demora <= 0) return; // ya pasó la hora

    // Guardamos el timer en un Map para no duplicar
    if (self._timers) clearTimeout(self._timers[id]);
    if (!self._timers) self._timers = {};

    self._timers[id] = setTimeout(() => {
      self.registration.showNotification(titulo, {
        body: cuerpo,
        icon: '/static/icon-192.png',
        badge: '/static/icon-192.png',
        vibrate: [200, 100, 200],
        tag: `tarea-${id}`,        // evita duplicados
        renotify: true,
        data: { id }
      });
    }, demora);
  }

  if (e.data && e.data.tipo === 'cancelar') {
    if (self._timers && self._timers[e.data.id]) {
      clearTimeout(self._timers[e.data.id]);
      delete self._timers[e.data.id];
    }
  }
});

// Al tocar la notificación, abre la app
self.addEventListener('notificationclick', e => {
  e.notification.close();
  e.waitUntil(
    self.clients.matchAll({ type: 'window' }).then(clients => {
      if (clients.length > 0) {
        clients[0].focus();
      } else {
        self.clients.openWindow('/');
      }
    })
  );
});
