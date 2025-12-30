// SoulHaven Service Worker
const CACHE_NAME = 'soulhaven-v12';
const OFFLINE_URL = '/offline.html';

// Arquivos para cachear
const STATIC_ASSETS = [
  '/',
  '/app',
  '/offline.html',
  '/manifest.json',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png',
  '/static/icons/logo-full.png',
  '/static/icons/logo-header.png'
];

// Instalação do Service Worker
self.addEventListener('install', (event) => {
  console.log('[SW] Installing Service Worker');
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] Caching static assets');
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// Ativação - limpa caches antigos
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating Service Worker');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => {
            console.log('[SW] Deleting old cache:', name);
            return caches.delete(name);
          })
      );
    })
  );
  self.clients.claim();
});

// Estratégia: Network First com fallback para cache
self.addEventListener('fetch', (event) => {
  // Ignora requisições não-GET
  if (event.request.method !== 'GET') return;

  // Ignora requisições de API (sempre buscar do servidor)
  if (event.request.url.includes('/api/')) {
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Clone a resposta para cachear
        if (response.status === 200) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
        }
        return response;
      })
      .catch(() => {
        // Fallback para cache se offline
        return caches.match(event.request).then((cachedResponse) => {
          if (cachedResponse) {
            return cachedResponse;
          }
          // Se for navegação, mostrar página offline
          if (event.request.mode === 'navigate') {
            return caches.match(OFFLINE_URL);
          }
          return new Response('Offline', { status: 503 });
        });
      })
  );
});

// ============================================
// PUSH NOTIFICATIONS
// ============================================

self.addEventListener('push', (event) => {
  console.log('[SW] Push received');

  let data = {
    title: 'SoulHaven',
    body: 'Voce tem uma nova mensagem',
    icon: '/static/icons/icon-192x192.png',
    url: '/app'
  };

  if (event.data) {
    try {
      data = { ...data, ...event.data.json() };
    } catch (e) {
      console.error('[SW] Error parsing push data:', e);
      data.body = event.data.text();
    }
  }

  const options = {
    body: data.body,
    icon: data.icon || '/static/icons/icon-192x192.png',
    badge: '/static/icons/icon-72x72.png',
    vibrate: [100, 50, 100],
    tag: data.tag || 'soulhaven-notification',
    renotify: true,
    requireInteraction: false,
    data: {
      url: data.url || '/app',
      timestamp: Date.now()
    },
    actions: [
      {
        action: 'open',
        title: 'Abrir'
      },
      {
        action: 'close',
        title: 'Fechar'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Clique em notificacao
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification clicked:', event.action);

  event.notification.close();

  // Se clicou em "fechar", nao faz nada
  if (event.action === 'close') {
    return;
  }

  // Abrir ou focar na janela do app
  const urlToOpen = event.notification.data?.url || '/app';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((windowClients) => {
        // Procurar janela existente
        for (const client of windowClients) {
          if (client.url.includes('/app') && 'focus' in client) {
            return client.focus();
          }
        }
        // Abrir nova janela se nao encontrou
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
  );
});

// Fechar notificacao
self.addEventListener('notificationclose', (event) => {
  console.log('[SW] Notification closed');
});

// Receber mensagens do cliente
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
