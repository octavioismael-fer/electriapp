// ElectriApp Service Worker — notificaciones con verificación periódica

self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));

// Guardamos las tareas programadas en memoria del SW
let tareasProgramadas = [];

// Cada vez que la app abre, recibe la lista actualizada de tareas
self.addEventListener('message', e => {
  if (e.data && e.data.tipo === 'tareas') {
    tareasProgramadas = e.data.tareas;
    console.log('[SW] Tareas recibidas:', tareasProgramadas.length);
  }
  if (e.data && e.data.tipo === 'cancelar') {
    tareasProgramadas = tareasProgramadas.filter(t => t.id !== e.data.id);
  }
});

// Verificación periódica cada 55 segundos via sync o fetch
// Usamos el evento de fetch para "despertar" el SW y verificar
self.addEventListener('fetch', e => {
  verificarTareas();
});

// También verificamos al activar
self.addEventListener('activate', e => {
  e.waitUntil(self.clients.claim());
  iniciarVerificacion();
});

function iniciarVerificacion() {
  // Fetch a nuestra propia API para mantener el SW activo y obtener tareas
  setInterval(async () => {
    await verificarTareas();
  }, 60 * 1000); // cada 60 segundos
}

async function verificarTareas() {
  try {
    // Obtenemos las tareas directo desde la API (sin depender de mensajes)
    const res = await fetch('/api/tareas-pendientes');
    if (!res.ok) return;
    const tareas = await res.json();
    const ahora = Date.now();

    for (const t of tareas) {
      if (!t.tarea_datetime) continue;
      const horaTrabajo = new Date(t.tarea_datetime).getTime();
      const minutosRestantes = (horaTrabajo - ahora) / 60000;

      // Notificar si faltan entre 14 y 16 minutos (ventana de 2 min para no duplicar)
      if (minutosRestantes >= 14 && minutosRestantes <= 16) {
        // Chequeamos que no hayamos notificado ya esta tarea
        const notifTag = `tarea-${t.id}-aviso`;
        const notifs = await self.registration.getNotifications({ tag: notifTag });
        if (notifs.length === 0) {
          await self.registration.showNotification(`⚡ ElectriApp — ${t.cliente}`, {
            body: `En ~15 min: ${t.descripcion}`,
            icon: '/static/icon-192.png',
            badge: '/static/icon-192.png',
            vibrate: [200, 100, 200, 100, 200],
            tag: notifTag,
            requireInteraction: true,  // no desaparece sola
            data: { id: t.id }
          });
        }
      }

      // Segunda notificación: en el momento exacto
      if (minutosRestantes >= -1 && minutosRestantes < 1) {
        const notifTag = `tarea-${t.id}-ahora`;
        const notifs = await self.registration.getNotifications({ tag: notifTag });
        if (notifs.length === 0) {
          await self.registration.showNotification(`🔧 ¡Ahora! — ${t.cliente}`, {
            body: t.descripcion,
            icon: '/static/icon-192.png',
            badge: '/static/icon-192.png',
            vibrate: [300, 100, 300, 100, 300],
            tag: notifTag,
            requireInteraction: true,
            data: { id: t.id }
          });
        }
      }
    }
  } catch(e) {
    // Silencioso si no hay conexión
  }
}

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
