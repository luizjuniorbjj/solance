"""
SoulHaven - Notification Scheduler
Sistema de lembretes automaticos e notificacoes de engajamento
Com retry logic, rate limiting e suporte a timezone
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import random
import logging
from collections import defaultdict

from app.database import get_db
from app.routes.push import send_push_notification

# Configurar logging
logger = logging.getLogger(__name__)

# ============================================
# CONFIGURACOES
# ============================================

# Rate limiting: max notificacoes por minuto
MAX_NOTIFICATIONS_PER_MINUTE = 50

# Retry config
MAX_RETRIES = 3
RETRY_DELAYS = [5, 30, 120]  # segundos entre retries

# Batch size para processamento
BATCH_SIZE = 20

# ============================================
# MENSAGENS DE LEMBRETE
# ============================================

REMINDER_MESSAGES = [
    {
        "title": "Momento de Reflexao",
        "body": "Reserve alguns minutos para conversar com Deus. Estou aqui para te ouvir."
    },
    {
        "title": "Como voce esta hoje?",
        "body": "Um novo dia, novas gracas. Quer compartilhar algo?"
    },
    {
        "title": "Hora de Paz",
        "body": "Pare um momento. Respire. Deus esta com voce."
    },
    {
        "title": "Lembrete Diario",
        "body": "Nao se esqueca: voce e amado. Quer conversar?"
    },
    {
        "title": "Devocional do Dia",
        "body": "Um versiculo pode mudar seu dia. Vamos refletir juntos?"
    },
    {
        "title": "Momento de Gratidao",
        "body": "Pelo que voce e grato hoje? Compartilhe comigo."
    },
    {
        "title": "Paz Interior",
        "body": "Entregue suas preocupacoes a Deus. Estou aqui para ajudar."
    },
    {
        "title": "Reflexao Matinal",
        "body": "Comece o dia com proposito. O que esta em seu coracao?"
    }
]

# ============================================
# MENSAGENS DE ENGAJAMENTO
# ============================================

ENGAGEMENT_MESSAGES = [
    {
        "title": "Sentimos sua falta!",
        "body": "Ja faz alguns dias. Como voce esta? Estou aqui quando precisar."
    },
    {
        "title": "Ola! Tudo bem?",
        "body": "Nao conversamos recentemente. Espero que esteja bem!"
    },
    {
        "title": "Estou aqui por voce",
        "body": "Sempre que precisar de apoio, pode contar comigo."
    },
    {
        "title": "Voltou a pensar em voce",
        "body": "Como estao as coisas? Quer conversar sobre algo?"
    },
    {
        "title": "Uma palavra de fe",
        "body": "Deus nao te esqueceu. Volte quando puder, estou aqui."
    }
]


# ============================================
# FILA DE RETRY
# ============================================

class RetryQueue:
    """Fila de notificacoes para retry com backoff exponencial"""

    def __init__(self):
        self.queue: List[Dict] = []
        self.processing = False

    def add(self, notification: Dict, retry_count: int = 0):
        """Adiciona notificacao na fila de retry"""
        if retry_count < MAX_RETRIES:
            delay = RETRY_DELAYS[min(retry_count, len(RETRY_DELAYS) - 1)]
            notification["retry_count"] = retry_count + 1
            notification["retry_at"] = datetime.now() + timedelta(seconds=delay)
            self.queue.append(notification)
            logger.info(f"[RETRY] Added to queue, retry #{retry_count + 1} in {delay}s")

    async def process(self, db):
        """Processa notificacoes prontas para retry"""
        if self.processing:
            return

        self.processing = True
        now = datetime.now()

        # Separar prontas para retry
        ready = [n for n in self.queue if n["retry_at"] <= now]
        self.queue = [n for n in self.queue if n["retry_at"] > now]

        for notification in ready:
            try:
                success = await send_push_notification(
                    subscription_info=notification["subscription_info"],
                    title=notification["title"],
                    body=notification["body"],
                    url=notification.get("url", "/app"),
                    db=db,
                    user_id=notification.get("user_id"),
                    notification_type=notification.get("notification_type", "retry")
                )

                if not success:
                    # Falhou novamente, adicionar de volta se ainda tem retries
                    self.add(notification, notification["retry_count"])

            except Exception as e:
                logger.error(f"[RETRY] Error processing retry: {e}")
                self.add(notification, notification["retry_count"])

        self.processing = False
        return len(ready)

# Instancia global da fila de retry
retry_queue = RetryQueue()


# ============================================
# RATE LIMITER
# ============================================

class RateLimiter:
    """Rate limiter para controlar envio de notificacoes"""

    def __init__(self, max_per_minute: int = MAX_NOTIFICATIONS_PER_MINUTE):
        self.max_per_minute = max_per_minute
        self.timestamps: List[datetime] = []

    def can_send(self) -> bool:
        """Verifica se pode enviar mais notificacoes"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)

        # Limpar timestamps antigos
        self.timestamps = [ts for ts in self.timestamps if ts > minute_ago]

        return len(self.timestamps) < self.max_per_minute

    def record_send(self):
        """Registra um envio"""
        self.timestamps.append(datetime.now())

    async def wait_if_needed(self):
        """Aguarda se necessario pelo rate limit"""
        while not self.can_send():
            await asyncio.sleep(1)

# Instancia global do rate limiter
rate_limiter = RateLimiter()


# ============================================
# TIMEZONE HELPER
# ============================================

# Mapeamento de timezones comuns do Brasil
TIMEZONE_OFFSETS = {
    "America/Sao_Paulo": -3,
    "America/Manaus": -4,
    "America/Belem": -3,
    "America/Fortaleza": -3,
    "America/Recife": -3,
    "America/Cuiaba": -4,
    "America/Porto_Velho": -4,
    "America/Rio_Branco": -5,
    "America/Noronha": -2,
    "UTC": 0,
    None: -3,  # Default: Brasilia
    "": -3,
}

def get_user_local_hour(utc_hour: int, timezone: Optional[str]) -> int:
    """Converte hora UTC para hora local do usuario"""
    offset = TIMEZONE_OFFSETS.get(timezone, -3)
    local_hour = (utc_hour + offset) % 24
    return local_hour


# ============================================
# SCHEDULER FUNCTIONS
# ============================================

async def send_notification_with_retry(
    subscription_info: Dict,
    title: str,
    body: str,
    url: str,
    db,
    user_id: str,
    notification_type: str
) -> bool:
    """Envia notificacao com suporte a retry"""
    try:
        await rate_limiter.wait_if_needed()

        success = await send_push_notification(
            subscription_info=subscription_info,
            title=title,
            body=body,
            url=url,
            db=db,
            user_id=user_id,
            notification_type=notification_type
        )

        if success:
            rate_limiter.record_send()
            return True
        else:
            # Adicionar na fila de retry
            retry_queue.add({
                "subscription_info": subscription_info,
                "title": title,
                "body": body,
                "url": url,
                "user_id": user_id,
                "notification_type": notification_type
            })
            return False

    except Exception as e:
        logger.error(f"[NOTIFICATION] Error sending: {e}")
        retry_queue.add({
            "subscription_info": subscription_info,
            "title": title,
            "body": body,
            "url": url,
            "user_id": user_id,
            "notification_type": notification_type
        })
        return False


async def send_reminder_notifications():
    """
    Envia lembretes para usuarios que configuraram horario.
    Considera timezone do usuario.
    """
    db = await get_db()
    utc_now = datetime.utcnow()
    utc_hour = utc_now.hour

    # Mapear dia da semana
    days_map = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    current_day = days_map[utc_now.weekday()]

    logger.info(f"[SCHEDULER] Checking reminders for UTC hour {utc_hour}, day {current_day}")

    sent_count = 0
    failed_count = 0

    try:
        # Buscar usuarios que querem lembrete nesta hora (considerando timezone)
        users = await db.get_users_for_reminder_with_timezone(utc_hour, current_day)
        logger.info(f"[SCHEDULER] Found {len(users)} users for reminder")

        # Processar em batches
        for i in range(0, len(users), BATCH_SIZE):
            batch = users[i:i + BATCH_SIZE]

            tasks = []
            for user in batch:
                message = random.choice(REMINDER_MESSAGES)

                subscription_info = {
                    "endpoint": user["endpoint"],
                    "keys": {
                        "p256dh": user["p256dh"],
                        "auth": user["auth"]
                    }
                }

                tasks.append(
                    send_notification_with_retry(
                        subscription_info=subscription_info,
                        title=message["title"],
                        body=message["body"],
                        url="/app",
                        db=db,
                        user_id=str(user["user_id"]),
                        notification_type="reminder"
                    )
                )

            # Executar batch
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if result is True:
                    sent_count += 1
                else:
                    failed_count += 1

            # Pequena pausa entre batches
            if i + BATCH_SIZE < len(users):
                await asyncio.sleep(2)

        logger.info(f"[SCHEDULER] Reminders: {sent_count} sent, {failed_count} failed")
        return sent_count

    except Exception as e:
        logger.error(f"[SCHEDULER] Error sending reminders: {e}")
        return 0


async def send_engagement_notifications():
    """
    Envia notificacoes para usuarios inativos.
    Processamento em batches com rate limiting.
    """
    db = await get_db()

    logger.info("[SCHEDULER] Checking engagement notifications")

    sent_count = 0
    failed_count = 0

    try:
        # Usar paginacao para usuarios inativos
        offset = 0
        limit = 100

        while True:
            users = await db.get_users_for_engagement(limit=limit, offset=offset)

            if not users:
                break

            logger.info(f"[SCHEDULER] Processing {len(users)} inactive users (offset {offset})")

            for i in range(0, len(users), BATCH_SIZE):
                batch = users[i:i + BATCH_SIZE]

                tasks = []
                for user in batch:
                    message = random.choice(ENGAGEMENT_MESSAGES)

                    subscription_info = {
                        "endpoint": user["endpoint"],
                        "keys": {
                            "p256dh": user["p256dh"],
                            "auth": user["auth"]
                        }
                    }

                    tasks.append(
                        send_notification_with_retry(
                            subscription_info=subscription_info,
                            title=message["title"],
                            body=message["body"],
                            url="/app",
                            db=db,
                            user_id=str(user["user_id"]),
                            notification_type="engagement"
                        )
                    )

                results = await asyncio.gather(*tasks, return_exceptions=True)

                for result in results:
                    if result is True:
                        sent_count += 1
                    else:
                        failed_count += 1

                # Pausa entre batches
                await asyncio.sleep(2)

            offset += limit

            # Safety limit
            if offset > 10000:
                logger.warning("[SCHEDULER] Safety limit reached for engagement")
                break

        logger.info(f"[SCHEDULER] Engagement: {sent_count} sent, {failed_count} failed")
        return sent_count

    except Exception as e:
        logger.error(f"[SCHEDULER] Error sending engagement notifications: {e}")
        return 0


# ============================================
# BACKGROUND SCHEDULER
# ============================================

class NotificationScheduler:
    """
    Scheduler robusto que roda em background para enviar notificacoes.
    Com retry queue, rate limiting e tratamento de erros.
    """

    def __init__(self):
        self.running = False
        self.task = None
        self.retry_task = None
        self.last_reminder_check = None
        self.last_engagement_check = None
        self.stats = {
            "reminders_sent": 0,
            "engagement_sent": 0,
            "retries_processed": 0,
            "errors": 0
        }

    async def start(self):
        """Inicia o scheduler em background"""
        if self.running:
            return

        self.running = True
        self.task = asyncio.create_task(self._run_loop())
        self.retry_task = asyncio.create_task(self._retry_loop())
        logger.info("[SCHEDULER] Notification scheduler started")

    async def stop(self):
        """Para o scheduler"""
        self.running = False

        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        if self.retry_task:
            self.retry_task.cancel()
            try:
                await self.retry_task
            except asyncio.CancelledError:
                pass

        logger.info("[SCHEDULER] Notification scheduler stopped")
        logger.info(f"[SCHEDULER] Final stats: {self.stats}")

    async def _run_loop(self):
        """Loop principal do scheduler"""
        while self.running:
            try:
                now = datetime.utcnow()

                # Enviar lembretes a cada hora (nos primeiros 5 minutos)
                should_send_reminders = (
                    now.minute < 5 and
                    (self.last_reminder_check is None or
                     self.last_reminder_check.hour != now.hour or
                     self.last_reminder_check.day != now.day)
                )

                if should_send_reminders:
                    count = await send_reminder_notifications()
                    self.stats["reminders_sent"] += count
                    self.last_reminder_check = now

                # Enviar engajamento uma vez por dia (as 13h UTC = 10h Brasilia)
                should_send_engagement = (
                    now.hour == 13 and
                    (self.last_engagement_check is None or
                     self.last_engagement_check.day != now.day)
                )

                if should_send_engagement:
                    count = await send_engagement_notifications()
                    self.stats["engagement_sent"] += count
                    self.last_engagement_check = now

                # Esperar 1 minuto antes de verificar novamente
                await asyncio.sleep(60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[SCHEDULER] Error in main loop: {e}")
                self.stats["errors"] += 1
                await asyncio.sleep(60)

    async def _retry_loop(self):
        """Loop para processar fila de retry"""
        while self.running:
            try:
                db = await get_db()
                count = await retry_queue.process(db)
                if count:
                    self.stats["retries_processed"] += count

                # Verificar retry queue a cada 30 segundos
                await asyncio.sleep(30)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[SCHEDULER] Error in retry loop: {e}")
                await asyncio.sleep(30)

    def get_stats(self) -> Dict:
        """Retorna estatisticas do scheduler"""
        return {
            **self.stats,
            "retry_queue_size": len(retry_queue.queue),
            "rate_limit_remaining": rate_limiter.max_per_minute - len(rate_limiter.timestamps),
            "running": self.running
        }


# Instancia global do scheduler
notification_scheduler = NotificationScheduler()
