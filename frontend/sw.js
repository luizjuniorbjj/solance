// AiSyster Service Worker
const CACHE_NAME = 'aisyster-v2';
const OFFLINE_URL = '/offline.html';
const DB_NAME = 'aisyster-offline';
const DB_VERSION = 1;
const SYNC_TAG = 'sync-messages';

// Arquivos para cachear
const STATIC_ASSETS = [
  '/',
  '/app',
  '/offline.html',
  '/manifest.json',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png',
  '/static/icons/icon-192x192-maskable.png',
  '/static/icons/icon-512x512-maskable.png'
];

// ============================================
// INDEXEDDB HELPERS
// ============================================

function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;

      // Store para mensagens pendentes
      if (!db.objectStoreNames.contains('pendingMessages')) {
        const store = db.createObjectStore('pendingMessages', {
          keyPath: 'id',
          autoIncrement: true
        });
        store.createIndex('timestamp', 'timestamp', { unique: false });
        store.createIndex('conversationId', 'conversationId', { unique: false });
      }

      // Store para cache de conversas
      if (!db.objectStoreNames.contains('conversationCache')) {
        const convStore = db.createObjectStore('conversationCache', {
          keyPath: 'conversationId'
        });
        convStore.createIndex('lastUpdated', 'lastUpdated', { unique: false });
      }
    };
  });
}

async function savePendingMessage(message) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('pendingMessages', 'readwrite');
    const store = tx.objectStore('pendingMessages');

    const data = {
      ...message,
      timestamp: Date.now(),
      status: 'pending'
    };

    const request = store.add(data);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function getPendingMessages() {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('pendingMessages', 'readonly');
    const store = tx.objectStore('pendingMessages');
    const request = store.getAll();

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function deletePendingMessage(id) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('pendingMessages', 'readwrite');
    const store = tx.objectStore('pendingMessages');
    const request = store.delete(id);

    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

async function clearAllPendingMessages() {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('pendingMessages', 'readwrite');
    const store = tx.objectStore('pendingMessages');
    const request = store.clear();

    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

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
    title: 'AiSyster',
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
    tag: data.tag || 'aisyster-notification',
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
self.addEventListener('message', async (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  // Salvar mensagem para envio offline
  if (event.data && event.data.type === 'QUEUE_MESSAGE') {
    try {
      const messageId = await savePendingMessage(event.data.message);
      console.log('[SW] Message queued for sync:', messageId);

      // Registrar sync se disponível
      if ('sync' in self.registration) {
        await self.registration.sync.register(SYNC_TAG);
        console.log('[SW] Sync registered');
      }

      // Responder ao cliente
      if (event.ports && event.ports[0]) {
        event.ports[0].postMessage({ success: true, id: messageId });
      }
    } catch (error) {
      console.error('[SW] Error queuing message:', error);
      if (event.ports && event.ports[0]) {
        event.ports[0].postMessage({ success: false, error: error.message });
      }
    }
  }

  // Verificar status de conexão
  if (event.data && event.data.type === 'CHECK_PENDING') {
    try {
      const pending = await getPendingMessages();
      if (event.ports && event.ports[0]) {
        event.ports[0].postMessage({ pending: pending.length });
      }
    } catch (error) {
      if (event.ports && event.ports[0]) {
        event.ports[0].postMessage({ pending: 0, error: error.message });
      }
    }
  }

  // Limpar mensagens pendentes manualmente
  if (event.data && event.data.type === 'CLEAR_PENDING') {
    try {
      await clearAllPendingMessages();
      if (event.ports && event.ports[0]) {
        event.ports[0].postMessage({ success: true });
      }
    } catch (error) {
      if (event.ports && event.ports[0]) {
        event.ports[0].postMessage({ success: false, error: error.message });
      }
    }
  }
});

// ============================================
// BACKGROUND SYNC
// ============================================

self.addEventListener('sync', async (event) => {
  console.log('[SW] Sync event:', event.tag);

  if (event.tag === SYNC_TAG) {
    event.waitUntil(syncPendingMessages());
  }
});

async function syncPendingMessages() {
  console.log('[SW] Starting message sync...');

  try {
    const pendingMessages = await getPendingMessages();
    console.log('[SW] Found pending messages:', pendingMessages.length);

    if (pendingMessages.length === 0) {
      return;
    }

    // Notificar cliente que sync começou
    notifyClients({ type: 'SYNC_STARTED', count: pendingMessages.length });

    let successCount = 0;
    let failCount = 0;

    for (const msg of pendingMessages) {
      try {
        // Enviar mensagem para o servidor
        const response = await fetch('/chat/message', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${msg.token}`
          },
          body: JSON.stringify({
            message: msg.content,
            conversation_id: msg.conversationId,
            offline_id: msg.id,
            offline_timestamp: msg.timestamp
          })
        });

        if (response.ok) {
          await deletePendingMessage(msg.id);
          successCount++;
          console.log('[SW] Message synced:', msg.id);
        } else if (response.status === 401) {
          // Token expirado - notificar cliente
          notifyClients({ type: 'AUTH_EXPIRED', messageId: msg.id });
          break;
        } else {
          failCount++;
          console.error('[SW] Failed to sync message:', response.status);
        }
      } catch (error) {
        failCount++;
        console.error('[SW] Error syncing message:', error);
      }
    }

    // Notificar cliente do resultado
    notifyClients({
      type: 'SYNC_COMPLETED',
      success: successCount,
      failed: failCount
    });

    console.log(`[SW] Sync completed: ${successCount} success, ${failCount} failed`);

  } catch (error) {
    console.error('[SW] Sync error:', error);
    notifyClients({ type: 'SYNC_ERROR', error: error.message });
  }
}

// Helper para notificar todos os clientes
async function notifyClients(message) {
  const allClients = await clients.matchAll({ includeUncontrolled: true });
  allClients.forEach(client => {
    client.postMessage(message);
  });
}

// Periodic Sync para tentar sync quando há conexão
self.addEventListener('periodicsync', (event) => {
  if (event.tag === 'sync-pending-messages') {
    event.waitUntil(syncPendingMessages());
  }
});
