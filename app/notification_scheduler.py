"""
SoulHaven - Notification Scheduler
Sistema de lembretes automaticos e notificacoes de engajamento
"""

import asyncio
from datetime import datetime
from typing import List, Dict
import random

from app.database import get_db
from app.routes.push import send_push_notification


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
# SCHEDULER FUNCTIONS
# ============================================

async def send_reminder_notifications():
    """
    Envia lembretes para usuarios que configuraram horario.
    Deve ser chamado a cada hora pelo scheduler.
    """
    db = await get_db()
    now = datetime.now()
    current_hour = now.hour

    # Mapear dia da semana
    days_map = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    current_day = days_map[now.weekday()]

    print(f"[SCHEDULER] Checking reminders for hour {current_hour}, day {current_day}")

    try:
        users = await db.get_users_for_reminder(current_hour, current_day)
        print(f"[SCHEDULER] Found {len(users)} users for reminder")

        for user in users:
            # Escolher mensagem aleatoria
            message = random.choice(REMINDER_MESSAGES)

            subscription_info = {
                "endpoint": user["endpoint"],
                "keys": {
                    "p256dh": user["p256dh"],
                    "auth": user["auth"]
                }
            }

            await send_push_notification(
                subscription_info=subscription_info,
                title=message["title"],
                body=message["body"],
                url="/app",
                db=db,
                user_id=str(user["user_id"]),
                notification_type="reminder"
            )

        return len(users)

    except Exception as e:
        print(f"[SCHEDULER] Error sending reminders: {e}")
        return 0


async def send_engagement_notifications():
    """
    Envia notificacoes para usuarios inativos.
    Deve ser chamado uma vez por dia.
    """
    db = await get_db()

    print("[SCHEDULER] Checking engagement notifications")

    try:
        users = await db.get_users_for_engagement()
        print(f"[SCHEDULER] Found {len(users)} inactive users")

        for user in users:
            # Escolher mensagem aleatoria
            message = random.choice(ENGAGEMENT_MESSAGES)

            subscription_info = {
                "endpoint": user["endpoint"],
                "keys": {
                    "p256dh": user["p256dh"],
                    "auth": user["auth"]
                }
            }

            await send_push_notification(
                subscription_info=subscription_info,
                title=message["title"],
                body=message["body"],
                url="/app",
                db=db,
                user_id=str(user["user_id"]),
                notification_type="engagement"
            )

        return len(users)

    except Exception as e:
        print(f"[SCHEDULER] Error sending engagement notifications: {e}")
        return 0


# ============================================
# BACKGROUND SCHEDULER
# ============================================

class NotificationScheduler:
    """
    Scheduler que roda em background para enviar notificacoes.
    """

    def __init__(self):
        self.running = False
        self.task = None

    async def start(self):
        """Inicia o scheduler em background"""
        if self.running:
            return

        self.running = True
        self.task = asyncio.create_task(self._run_loop())
        print("[SCHEDULER] Notification scheduler started")

    async def stop(self):
        """Para o scheduler"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        print("[SCHEDULER] Notification scheduler stopped")

    async def _run_loop(self):
        """Loop principal do scheduler"""
        last_reminder_hour = -1
        last_engagement_day = -1

        while self.running:
            try:
                now = datetime.now()

                # Enviar lembretes a cada hora (no inicio da hora)
                if now.hour != last_reminder_hour and now.minute < 5:
                    await send_reminder_notifications()
                    last_reminder_hour = now.hour

                # Enviar notificacoes de engajamento uma vez por dia (as 10h)
                if now.hour == 10 and now.day != last_engagement_day:
                    await send_engagement_notifications()
                    last_engagement_day = now.day

                # Esperar 1 minuto antes de verificar novamente
                await asyncio.sleep(60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[SCHEDULER] Error in loop: {e}")
                await asyncio.sleep(60)


# Instancia global do scheduler
notification_scheduler = NotificationScheduler()
