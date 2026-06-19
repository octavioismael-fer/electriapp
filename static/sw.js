// ElectriApp Service Worker

self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));

self.addEventListener('message', e => {
  if (e.data && e.data.tipo === 'cancelar') {
    self.registration.getNotifications().then(notifs => {
      notifs.forEach(n => n.close());
    });
  }
});

// Recibe notificaciones push del servidor (vía Vercel Cron + pywebpush)
self.addEventListener('push', e => {
  let data = {};
  try { data = e.data ? e.data.json() : {}; } catch (_) {}
  const titulo = data.titulo || 'ElectriApp';
  const cuerpo = data.cuerpo || 'Tenés una tarea pendiente';
  e.waitUntil(
    self.registration.showNotification(titulo, {
      body: cuerpo,
      icon: '/static/icon-192.png',
      badge: '/static/icon-192.png',
    })
  );
});

// Al tocar la notificación, abre la app
self.addEventListener('notificationclick', e => {
  e.notification.close();
  e.waitUntil(
    self.clients.matchAll({ type: 'window' }).then(clients => {
      if (clients.length > 0) return clients[0].focus();
      return self.clients.openWindow('/');
    })
  );
});
