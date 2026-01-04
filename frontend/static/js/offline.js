/**
 * AiSyster Offline Support
 * Gerencia detecção de conexão, fila de mensagens e sincronização
 */

class OfflineManager {
  constructor() {
    this.isOnline = navigator.onLine;
    this.pendingCount = 0;
    this.listeners = [];
    this.swRegistration = null;

    this.init();
  }

  async init() {
    // Listeners de conexão
    window.addEventListener('online', () => this.handleOnline());
    window.addEventListener('offline', () => this.handleOffline());

    // Listener para mensagens do Service Worker
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.addEventListener('message', (event) => {
        this.handleSWMessage(event.data);
      });

      // Obter registration
      this.swRegistration = await navigator.serviceWorker.ready;
    }

    // Verificar mensagens pendentes
    await this.checkPending();

    // UI inicial
    this.updateUI();
  }

  // ============================================
  // EVENT HANDLERS
  // ============================================

  handleOnline() {
    console.log('[Offline] Conexão restaurada');
    this.isOnline = true;
    this.updateUI();
    this.notify('online');
    this.showToast('Conexão restaurada', 'success');

    // Tentar sync imediato
    this.triggerSync();
  }

  handleOffline() {
    console.log('[Offline] Conexão perdida');
    this.isOnline = false;
    this.updateUI();
    this.notify('offline');
    this.showToast('Você está offline. Mensagens serão enviadas quando a conexão voltar.', 'warning');
  }

  handleSWMessage(data) {
    switch (data.type) {
      case 'SYNC_STARTED':
        console.log('[Offline] Sync iniciado:', data.count, 'mensagens');
        this.showToast(`Sincronizando ${data.count} mensagens...`, 'info');
        break;

      case 'SYNC_COMPLETED':
        console.log('[Offline] Sync completo:', data.success, 'sucesso,', data.failed, 'falhas');
        if (data.success > 0) {
          this.showToast(`${data.success} mensagens sincronizadas!`, 'success');
        }
        if (data.failed > 0) {
          this.showToast(`${data.failed} mensagens falharam. Tentaremos novamente.`, 'warning');
        }
        this.checkPending();
        this.notify('sync-complete', data);
        break;

      case 'SYNC_ERROR':
        console.error('[Offline] Erro no sync:', data.error);
        this.showToast('Erro ao sincronizar. Tentaremos novamente.', 'error');
        break;

      case 'AUTH_EXPIRED':
        console.warn('[Offline] Token expirado');
        this.showToast('Sessão expirada. Faça login novamente.', 'error');
        this.notify('auth-expired');
        break;
    }
  }

  // ============================================
  // QUEUE MESSAGE
  // ============================================

  async queueMessage(message, conversationId, token) {
    if (!this.swRegistration) {
      console.error('[Offline] Service Worker não disponível');
      return { success: false, error: 'Service Worker não disponível' };
    }

    return new Promise((resolve) => {
      const messageChannel = new MessageChannel();

      messageChannel.port1.onmessage = (event) => {
        if (event.data.success) {
          this.pendingCount++;
          this.updateUI();
          resolve({ success: true, id: event.data.id });
        } else {
          resolve({ success: false, error: event.data.error });
        }
      };

      navigator.serviceWorker.controller.postMessage({
        type: 'QUEUE_MESSAGE',
        message: {
          content: message,
          conversationId: conversationId,
          token: token
        }
      }, [messageChannel.port2]);
    });
  }

  // ============================================
  // CHECK PENDING
  // ============================================

  async checkPending() {
    if (!this.swRegistration || !navigator.serviceWorker.controller) {
      return 0;
    }

    return new Promise((resolve) => {
      const messageChannel = new MessageChannel();

      messageChannel.port1.onmessage = (event) => {
        this.pendingCount = event.data.pending || 0;
        this.updateUI();
        resolve(this.pendingCount);
      };

      navigator.serviceWorker.controller.postMessage({
        type: 'CHECK_PENDING'
      }, [messageChannel.port2]);
    });
  }

  // ============================================
  // TRIGGER SYNC
  // ============================================

  async triggerSync() {
    if (!this.swRegistration) return;

    try {
      // Tentar Background Sync
      if ('sync' in this.swRegistration) {
        await this.swRegistration.sync.register('sync-messages');
        console.log('[Offline] Sync registrado');
      } else {
        // Fallback: forçar sync manual
        console.log('[Offline] Background Sync não suportado, tentando manual...');
        navigator.serviceWorker.controller.postMessage({ type: 'FORCE_SYNC' });
      }
    } catch (error) {
      console.error('[Offline] Erro ao registrar sync:', error);
    }
  }

  // ============================================
  // CLEAR PENDING
  // ============================================

  async clearPending() {
    if (!this.swRegistration || !navigator.serviceWorker.controller) {
      return false;
    }

    return new Promise((resolve) => {
      const messageChannel = new MessageChannel();

      messageChannel.port1.onmessage = (event) => {
        if (event.data.success) {
          this.pendingCount = 0;
          this.updateUI();
        }
        resolve(event.data.success);
      };

      navigator.serviceWorker.controller.postMessage({
        type: 'CLEAR_PENDING'
      }, [messageChannel.port2]);
    });
  }

  // ============================================
  // UI UPDATES
  // ============================================

  updateUI() {
    // Atualizar indicador de status
    const statusEl = document.getElementById('offlineStatus');
    if (statusEl) {
      if (!this.isOnline) {
        statusEl.innerHTML = `
          <div class="offline-indicator offline">
            <span class="offline-dot"></span>
            Offline
            ${this.pendingCount > 0 ? `<span class="pending-badge">${this.pendingCount}</span>` : ''}
          </div>
        `;
        statusEl.style.display = 'flex';
      } else if (this.pendingCount > 0) {
        statusEl.innerHTML = `
          <div class="offline-indicator syncing">
            <span class="sync-spinner"></span>
            Sincronizando ${this.pendingCount}...
          </div>
        `;
        statusEl.style.display = 'flex';
      } else {
        statusEl.style.display = 'none';
      }
    }

    // Atualizar classe do body
    document.body.classList.toggle('is-offline', !this.isOnline);
  }

  // ============================================
  // TOAST NOTIFICATIONS
  // ============================================

  showToast(message, type = 'info') {
    // Criar container se não existir
    let container = document.getElementById('toastContainer');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toastContainer';
      container.style.cssText = `
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 10000;
        display: flex;
        flex-direction: column;
        gap: 8px;
      `;
      document.body.appendChild(container);
    }

    // Criar toast
    const toast = document.createElement('div');
    toast.style.cssText = `
      padding: 12px 20px;
      border-radius: 8px;
      color: white;
      font-size: 14px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      animation: slideUp 0.3s ease;
      max-width: 300px;
      text-align: center;
    `;

    // Cores por tipo
    const colors = {
      success: '#10b981',
      error: '#ef4444',
      warning: '#f59e0b',
      info: '#3b82f6'
    };
    toast.style.background = colors[type] || colors.info;
    toast.textContent = message;

    container.appendChild(toast);

    // Auto remover
    setTimeout(() => {
      toast.style.animation = 'slideDown 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  // ============================================
  // LISTENERS
  // ============================================

  on(event, callback) {
    this.listeners.push({ event, callback });
  }

  off(event, callback) {
    this.listeners = this.listeners.filter(
      l => !(l.event === event && l.callback === callback)
    );
  }

  notify(event, data = null) {
    this.listeners
      .filter(l => l.event === event)
      .forEach(l => l.callback(data));
  }

  // ============================================
  // GETTERS
  // ============================================

  get online() {
    return this.isOnline;
  }

  get pending() {
    return this.pendingCount;
  }
}

// Criar instância global
window.offlineManager = new OfflineManager();

// Adicionar CSS para animações e indicadores
const offlineStyles = document.createElement('style');
offlineStyles.textContent = `
  @keyframes slideUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }

  @keyframes slideDown {
    from { opacity: 1; transform: translateY(0); }
    to { opacity: 0; transform: translateY(20px); }
  }

  .offline-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
  }

  .offline-indicator.offline {
    background: rgba(239, 68, 68, 0.1);
    color: #ef4444;
  }

  .offline-indicator.syncing {
    background: rgba(59, 130, 246, 0.1);
    color: #3b82f6;
  }

  .offline-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: currentColor;
    animation: pulse 1.5s infinite;
  }

  .sync-spinner {
    width: 14px;
    height: 14px;
    border: 2px solid currentColor;
    border-top-color: transparent;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .pending-badge {
    background: currentColor;
    color: white;
    padding: 2px 6px;
    border-radius: 10px;
    font-size: 10px;
  }

  body.is-offline .send-button:not(:disabled) {
    background: #f59e0b !important;
  }
`;
document.head.appendChild(offlineStyles);
