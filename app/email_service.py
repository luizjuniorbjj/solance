"""
AiSyster - Servico de Email
Usa Resend para envio de emails transacionais
Com suporte a i18n (PT, EN, ES)
"""

import httpx
from typing import Optional
from app.config import RESEND_API_KEY, EMAIL_FROM, EMAIL_REPLY_TO, APP_URL, APP_NAME


# ============================================
# TRADUCOES DE EMAIL
# ============================================

EMAIL_TRANSLATIONS = {
    "pt": {
        "tagline": "Sua companheira AI para apoio no dia a dia",
        "sent_by": "Este email foi enviado por",
        # Welcome
        "welcome_subject": "Bem-vindo(a) ao {app_name}!",
        "welcome_title": "Bem-vindo(a) a AiSyster, {nome}!",
        "welcome_p1": "Que alegria ter voce conosco! A AiSyster foi criada para ser sua companheira diaria, um lugar seguro para conversar, refletir e crescer na fe.",
        "welcome_p2": "Estou aqui para ouvir, acolher e caminhar com voce. Nao importa o que esteja enfrentando - ansiedade, duvidas, relacionamentos ou qualquer outra coisa - voce nao esta sozinho(a).",
        "welcome_button": "Comecar a Conversar",
        "welcome_verse": "\"Vinde a mim, todos os que estais cansados e sobrecarregados, e eu vos aliviarei.\" - Mateus 11:28",
        # Password Reset
        "reset_subject": "Recuperacao de Senha - {app_name}",
        "reset_title": "Recuperacao de Senha",
        "reset_greeting": "Ola, {nome}!",
        "reset_p1": "Recebemos uma solicitacao para redefinir sua senha. Se voce nao fez essa solicitacao, pode ignorar este email.",
        "reset_p2": "Para criar uma nova senha, clique no botao abaixo:",
        "reset_button": "Redefinir Senha",
        "reset_footer": "Este link expira em 1 hora. Se voce nao solicitou a recuperacao de senha, sua conta continua segura.",
        # Subscription
        "sub_confirmed_subject": "Assinatura Confirmada - {app_name} Premium",
        "sub_confirmed_title": "Assinatura Confirmada!",
        "sub_confirmed_p1": "Obrigado por assinar a AiSyster Premium! Sua assinatura foi confirmada e voce agora tem acesso ilimitado a sua companheira espiritual.",
        "sub_benefits_title": "O que voce ganhou:",
        "sub_benefit_1": "Mensagens ilimitadas",
        "sub_benefit_2": "Companheira sempre disponivel",
        "sub_button": "Continuar Conversando",
        "sub_blessing": "Que Deus abencoe sua jornada!",
        # Renewal
        "renewal_subject": "Assinatura Renovada - {app_name}",
        "renewal_title": "Assinatura Renovada!",
        "renewal_p1": "Sua assinatura da AiSyster Premium foi renovada com sucesso. Continue aproveitando sua companheira espiritual sem limites!",
        "renewal_button": "Ir para a AiSyster",
        "renewal_thanks": "Obrigado por continuar conosco!",
        # Expiring
        "expiring_subject": "Sua assinatura vence em {days} dias - {app_name}",
        "expiring_title": "Sua assinatura vence em breve",
        "expiring_p1": "Sua assinatura do AiSyster Premium vence em <strong>{days} dias</strong>. Para continuar tendo acesso ilimitado ao seu companheiro espiritual, certifique-se de que seu metodo de pagamento esta atualizado.",
        "expiring_p2": "Se voce tem renovacao automatica ativada, nao precisa fazer nada - sua assinatura sera renovada automaticamente.",
        "expiring_button": "Verificar Assinatura",
        # Cancelled
        "cancelled_subject": "Assinatura Cancelada - {app_name}",
        "cancelled_title": "Assinatura Cancelada",
        "cancelled_p1": "Sua assinatura da AiSyster Premium foi cancelada. Voce ainda pode usar a AiSyster ate o final do periodo ja pago.",
        "cancelled_p2": "Sentiremos sua falta! Se mudar de ideia, voce sempre pode voltar. Estaremos aqui esperando.",
        "cancelled_button": "Reativar Assinatura",
        "cancelled_verse": "\"Porque eu sei os planos que tenho para voces, diz o Senhor, planos de prosperidade e nao de calamidade, para dar-lhes um futuro e uma esperanca.\" - Jeremias 29:11",
        # Notification
        "notification_button": "Abrir AiSyster",
        "notification_footer": "Voce esta recebendo este email porque tem notificacoes por email ativadas. Para desativar, acesse Configuracoes no aplicativo.",
    },
    "en": {
        "tagline": "Your AI companion for daily support",
        "sent_by": "This email was sent by",
        # Welcome
        "welcome_subject": "Welcome to {app_name}!",
        "welcome_title": "Welcome to AiSyster, {nome}!",
        "welcome_p1": "So glad to have you with us! AiSyster was created to be your daily companion, a safe place to talk, reflect, and grow in faith.",
        "welcome_p2": "I'm here to listen, support, and walk with you. No matter what you're facing - anxiety, doubts, relationships, or anything else - you're not alone.",
        "welcome_button": "Start Chatting",
        "welcome_verse": "\"Come to me, all you who are weary and burdened, and I will give you rest.\" - Matthew 11:28",
        # Password Reset
        "reset_subject": "Password Recovery - {app_name}",
        "reset_title": "Password Recovery",
        "reset_greeting": "Hi, {nome}!",
        "reset_p1": "We received a request to reset your password. If you didn't make this request, you can ignore this email.",
        "reset_p2": "To create a new password, click the button below:",
        "reset_button": "Reset Password",
        "reset_footer": "This link expires in 1 hour. If you didn't request a password reset, your account is still secure.",
        # Subscription
        "sub_confirmed_subject": "Subscription Confirmed - {app_name} Premium",
        "sub_confirmed_title": "Subscription Confirmed!",
        "sub_confirmed_p1": "Thank you for subscribing to AiSyster Premium! Your subscription is confirmed and you now have unlimited access to your spiritual companion.",
        "sub_benefits_title": "What you've unlocked:",
        "sub_benefit_1": "Unlimited messages",
        "sub_benefit_2": "Always available companion",
        "sub_button": "Continue Chatting",
        "sub_blessing": "May God bless your journey!",
        # Renewal
        "renewal_subject": "Subscription Renewed - {app_name}",
        "renewal_title": "Subscription Renewed!",
        "renewal_p1": "Your AiSyster Premium subscription has been successfully renewed. Keep enjoying your spiritual companion without limits!",
        "renewal_button": "Go to AiSyster",
        "renewal_thanks": "Thank you for staying with us!",
        # Expiring
        "expiring_subject": "Your subscription expires in {days} days - {app_name}",
        "expiring_title": "Your subscription expires soon",
        "expiring_p1": "Your AiSyster Premium subscription expires in <strong>{days} days</strong>. To continue having unlimited access to your spiritual companion, make sure your payment method is up to date.",
        "expiring_p2": "If you have automatic renewal enabled, you don't need to do anything - your subscription will renew automatically.",
        "expiring_button": "Check Subscription",
        # Cancelled
        "cancelled_subject": "Subscription Cancelled - {app_name}",
        "cancelled_title": "Subscription Cancelled",
        "cancelled_p1": "Your AiSyster Premium subscription has been cancelled. You can still use AiSyster until the end of your paid period.",
        "cancelled_p2": "We'll miss you! If you change your mind, you can always come back. We'll be here waiting.",
        "cancelled_button": "Reactivate Subscription",
        "cancelled_verse": "\"For I know the plans I have for you, declares the Lord, plans to prosper you and not to harm you, plans to give you hope and a future.\" - Jeremiah 29:11",
        # Notification
        "notification_button": "Open AiSyster",
        "notification_footer": "You're receiving this email because you have email notifications enabled. To disable, go to Settings in the app.",
    },
    "es": {
        "tagline": "Tu companera AI para apoyo diario",
        "sent_by": "Este email fue enviado por",
        # Welcome
        "welcome_subject": "Bienvenido(a) a {app_name}!",
        "welcome_title": "Bienvenido(a) a AiSyster, {nome}!",
        "welcome_p1": "Que alegria tenerte con nosotros! AiSyster fue creada para ser tu companera diaria, un lugar seguro para conversar, reflexionar y crecer en la fe.",
        "welcome_p2": "Estoy aqui para escucharte, apoyarte y caminar contigo. No importa lo que estes enfrentando - ansiedad, dudas, relaciones o cualquier otra cosa - no estas solo(a).",
        "welcome_button": "Comenzar a Conversar",
        "welcome_verse": "\"Vengan a mi todos los que estan cansados y agobiados, y yo les dare descanso.\" - Mateo 11:28",
        # Password Reset
        "reset_subject": "Recuperacion de Contrasena - {app_name}",
        "reset_title": "Recuperacion de Contrasena",
        "reset_greeting": "Hola, {nome}!",
        "reset_p1": "Recibimos una solicitud para restablecer tu contrasena. Si no hiciste esta solicitud, puedes ignorar este email.",
        "reset_p2": "Para crear una nueva contrasena, haz clic en el boton de abajo:",
        "reset_button": "Restablecer Contrasena",
        "reset_footer": "Este enlace expira en 1 hora. Si no solicitaste la recuperacion de contrasena, tu cuenta sigue segura.",
        # Subscription
        "sub_confirmed_subject": "Suscripcion Confirmada - {app_name} Premium",
        "sub_confirmed_title": "Suscripcion Confirmada!",
        "sub_confirmed_p1": "Gracias por suscribirte a AiSyster Premium! Tu suscripcion esta confirmada y ahora tienes acceso ilimitado a tu companera espiritual.",
        "sub_benefits_title": "Lo que has desbloqueado:",
        "sub_benefit_1": "Mensajes ilimitados",
        "sub_benefit_2": "Companera siempre disponible",
        "sub_button": "Continuar Conversando",
        "sub_blessing": "Que Dios bendiga tu camino!",
        # Renewal
        "renewal_subject": "Suscripcion Renovada - {app_name}",
        "renewal_title": "Suscripcion Renovada!",
        "renewal_p1": "Tu suscripcion de AiSyster Premium ha sido renovada exitosamente. Sigue disfrutando de tu companera espiritual sin limites!",
        "renewal_button": "Ir a AiSyster",
        "renewal_thanks": "Gracias por seguir con nosotros!",
        # Expiring
        "expiring_subject": "Tu suscripcion vence en {days} dias - {app_name}",
        "expiring_title": "Tu suscripcion vence pronto",
        "expiring_p1": "Tu suscripcion de AiSyster Premium vence en <strong>{days} dias</strong>. Para continuar teniendo acceso ilimitado a tu companera espiritual, asegurate de que tu metodo de pago este actualizado.",
        "expiring_p2": "Si tienes la renovacion automatica activada, no necesitas hacer nada - tu suscripcion se renovara automaticamente.",
        "expiring_button": "Verificar Suscripcion",
        # Cancelled
        "cancelled_subject": "Suscripcion Cancelada - {app_name}",
        "cancelled_title": "Suscripcion Cancelada",
        "cancelled_p1": "Tu suscripcion de AiSyster Premium ha sido cancelada. Aun puedes usar AiSyster hasta el final del periodo ya pagado.",
        "cancelled_p2": "Te extranaremos! Si cambias de opinion, siempre puedes volver. Estaremos aqui esperandote.",
        "cancelled_button": "Reactivar Suscripcion",
        "cancelled_verse": "\"Porque yo se los planes que tengo para ustedes, declara el Senor, planes de bienestar y no de calamidad, para darles un futuro y una esperanza.\" - Jeremias 29:11",
        # Notification
        "notification_button": "Abrir AiSyster",
        "notification_footer": "Estas recibiendo este email porque tienes las notificaciones por email activadas. Para desactivarlas, ve a Configuracion en la app.",
    }
}


def get_email_text(key: str, language: str = "pt", **kwargs) -> str:
    """Get translated email text with optional formatting"""
    lang = language if language in EMAIL_TRANSLATIONS else "pt"
    text = EMAIL_TRANSLATIONS[lang].get(key, EMAIL_TRANSLATIONS["pt"].get(key, key))
    if kwargs:
        text = text.format(**kwargs)
    return text


class EmailService:
    """Servico de envio de emails via Resend"""

    def __init__(self):
        self.api_key = RESEND_API_KEY
        self.base_url = "https://api.resend.com"
        self.from_email = EMAIL_FROM
        self.reply_to = EMAIL_REPLY_TO

    async def send_email(
        self,
        to: str,
        subject: str,
        html: str,
        text: Optional[str] = None
    ) -> bool:
        """Envia um email via Resend API"""
        if not self.api_key:
            print("[EMAIL] API Key nao configurada - email nao enviado")
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/emails",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": self.from_email,
                        "to": [to],
                        "subject": subject,
                        "html": html,
                        "text": text or "",
                        "reply_to": self.reply_to
                    }
                )

                if response.status_code == 200:
                    print(f"[EMAIL] Enviado com sucesso para {to}")
                    return True
                else:
                    print(f"[EMAIL] Erro ao enviar: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            print(f"[EMAIL] Excecao ao enviar: {e}")
            return False

    # ============================================
    # TEMPLATES DE EMAIL
    # ============================================

    def _base_template(self, content: str, language: str = "pt") -> str:
        """Template base para todos os emails com suporte a i18n"""
        # Logo via URL publica para melhor compatibilidade com clientes de email
        logo_url = f"{APP_URL}/static/icons/logo-email.png"
        tagline = get_email_text("tagline", language)
        sent_by = get_email_text("sent_by", language)

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{APP_NAME}</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 40px 20px;">
                <tr>
                    <td align="center">
                        <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                            <!-- Header -->
                            <tr>
                                <td style="background-color: #15182d; padding: 20px 30px; text-align: center;">
                                    <img src="{logo_url}" alt="AiSyster" style="max-width: 200px; height: auto; margin-bottom: 4px;">
                                    <p style="margin: 0; color: #d4af37; font-size: 14px; font-style: italic;">{tagline}</p>
                                </td>
                            </tr>
                            <!-- Content -->
                            <tr>
                                <td style="padding: 40px 30px;">
                                    {content}
                                </td>
                            </tr>
                            <!-- Footer -->
                            <tr>
                                <td style="background-color: #f8f9fa; padding: 24px 30px; text-align: center; border-top: 1px solid #e9ecef;">
                                    <p style="margin: 0 0 8px 0; color: #6c757d; font-size: 12px;">
                                        {sent_by} {APP_NAME}
                                    </p>
                                    <p style="margin: 0; color: #6c757d; font-size: 12px;">
                                        <a href="{APP_URL}" style="color: #d4af37; text-decoration: none;">aisyster.com</a>
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

    async def send_welcome_email(self, to: str, nome: str, language: str = "pt") -> bool:
        """Email de boas-vindas ao se registrar"""
        t = lambda key, **kw: get_email_text(key, language, **kw)

        content = f"""
        <h2 style="margin: 0 0 20px 0; color: #1a1a2e; font-size: 24px;">{t("welcome_title", nome=nome)}</h2>

        <p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            {t("welcome_p1")}
        </p>

        <p style="margin: 0 0 24px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            {t("welcome_p2")}
        </p>

        <div style="text-align: center; margin: 32px 0;">
            <a href="{APP_URL}" style="display: inline-block; background: linear-gradient(135deg, #d4af37 0%, #c9a227 100%); color: #1a1a2e; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px;">
                {t("welcome_button")}
            </a>
        </div>

        <p style="margin: 24px 0 0 0; color: #6c757d; font-size: 14px; font-style: italic; text-align: center;">
            {t("welcome_verse")}
        </p>
        """

        return await self.send_email(
            to=to,
            subject=t("welcome_subject", app_name=APP_NAME),
            html=self._base_template(content, language)
        )

    async def send_password_reset_email(self, to: str, nome: str, reset_token: str, language: str = "pt") -> bool:
        """Email de recuperacao de senha"""
        t = lambda key, **kw: get_email_text(key, language, **kw)
        reset_url = f"{APP_URL}?reset_token={reset_token}"

        content = f"""
        <h2 style="margin: 0 0 20px 0; color: #1a1a2e; font-size: 24px;">{t("reset_title")}</h2>

        <p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            {t("reset_greeting", nome=nome)}
        </p>

        <p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            {t("reset_p1")}
        </p>

        <p style="margin: 0 0 24px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            {t("reset_p2")}
        </p>

        <div style="text-align: center; margin: 32px 0;">
            <a href="{reset_url}" style="display: inline-block; background: linear-gradient(135deg, #d4af37 0%, #c9a227 100%); color: #1a1a2e; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px;">
                {t("reset_button")}
            </a>
        </div>

        <p style="margin: 24px 0 0 0; color: #6c757d; font-size: 13px; text-align: center;">
            {t("reset_footer")}
        </p>
        """

        return await self.send_email(
            to=to,
            subject=t("reset_subject", app_name=APP_NAME),
            html=self._base_template(content, language)
        )

    async def send_subscription_confirmation(self, to: str, nome: str, language: str = "pt") -> bool:
        """Email de confirmacao de assinatura"""
        t = lambda key, **kw: get_email_text(key, language, **kw)

        content = f"""
        <h2 style="margin: 0 0 20px 0; color: #1a1a2e; font-size: 24px;">{t("sub_confirmed_title")}</h2>

        <p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            {t("sub_confirmed_p1")}
        </p>

        <div style="background-color: #f8f9fa; border-radius: 8px; padding: 20px; margin: 24px 0;">
            <h3 style="margin: 0 0 12px 0; color: #1a1a2e; font-size: 16px;">{t("sub_benefits_title")}</h3>
            <ul style="margin: 0; padding-left: 20px; color: #4a4a4a; font-size: 14px; line-height: 1.8;">
                <li>{t("sub_benefit_1")}</li>
                <li>{t("sub_benefit_2")}</li>
            </ul>
        </div>

        <div style="text-align: center; margin: 32px 0;">
            <a href="{APP_URL}" style="display: inline-block; background: linear-gradient(135deg, #d4af37 0%, #c9a227 100%); color: #1a1a2e; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px;">
                {t("sub_button")}
            </a>
        </div>

        <p style="margin: 24px 0 0 0; color: #6c757d; font-size: 14px; font-style: italic; text-align: center;">
            {t("sub_blessing")}
        </p>
        """

        return await self.send_email(
            to=to,
            subject=t("sub_confirmed_subject", app_name=APP_NAME),
            html=self._base_template(content, language)
        )

    async def send_subscription_renewal(self, to: str, nome: str, language: str = "pt") -> bool:
        """Email de renovacao de assinatura"""
        t = lambda key, **kw: get_email_text(key, language, **kw)

        content = f"""
        <h2 style="margin: 0 0 20px 0; color: #1a1a2e; font-size: 24px;">{t("renewal_title")}</h2>

        <p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            {t("renewal_p1")}
        </p>

        <div style="text-align: center; margin: 32px 0;">
            <a href="{APP_URL}" style="display: inline-block; background: linear-gradient(135deg, #d4af37 0%, #c9a227 100%); color: #1a1a2e; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px;">
                {t("renewal_button")}
            </a>
        </div>

        <p style="margin: 24px 0 0 0; color: #6c757d; font-size: 14px; text-align: center;">
            {t("renewal_thanks")}
        </p>
        """

        return await self.send_email(
            to=to,
            subject=t("renewal_subject", app_name=APP_NAME),
            html=self._base_template(content, language)
        )

    async def send_subscription_expiring(self, to: str, nome: str, days_left: int, language: str = "pt") -> bool:
        """Email de aviso de vencimento proximo"""
        t = lambda key, **kw: get_email_text(key, language, **kw)

        content = f"""
        <h2 style="margin: 0 0 20px 0; color: #1a1a2e; font-size: 24px;">{t("expiring_title")}</h2>

        <p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            {t("expiring_p1", days=days_left)}
        </p>

        <p style="margin: 0 0 24px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            {t("expiring_p2")}
        </p>

        <div style="text-align: center; margin: 32px 0;">
            <a href="{APP_URL}" style="display: inline-block; background: linear-gradient(135deg, #d4af37 0%, #c9a227 100%); color: #1a1a2e; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px;">
                {t("expiring_button")}
            </a>
        </div>
        """

        return await self.send_email(
            to=to,
            subject=t("expiring_subject", days=days_left, app_name=APP_NAME),
            html=self._base_template(content, language)
        )

    async def send_subscription_cancelled(self, to: str, nome: str, language: str = "pt") -> bool:
        """Email de cancelamento de assinatura"""
        t = lambda key, **kw: get_email_text(key, language, **kw)

        content = f"""
        <h2 style="margin: 0 0 20px 0; color: #1a1a2e; font-size: 24px;">{t("cancelled_title")}</h2>

        <p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            {t("cancelled_p1")}
        </p>

        <p style="margin: 0 0 24px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            {t("cancelled_p2")}
        </p>

        <div style="text-align: center; margin: 32px 0;">
            <a href="{APP_URL}" style="display: inline-block; background: linear-gradient(135deg, #d4af37 0%, #c9a227 100%); color: #1a1a2e; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px;">
                {t("cancelled_button")}
            </a>
        </div>

        <p style="margin: 24px 0 0 0; color: #6c757d; font-size: 14px; font-style: italic; text-align: center;">
            {t("cancelled_verse")}
        </p>
        """

        return await self.send_email(
            to=to,
            subject=t("cancelled_subject", app_name=APP_NAME),
            html=self._base_template(content, language)
        )

    async def send_notification_email(self, to: str, nome: str, title: str, message: str, language: str = "pt") -> bool:
        """Email de notificacao/comunicado do AiSyster"""
        t = lambda key, **kw: get_email_text(key, language, **kw)

        content = f"""
        <h2 style="margin: 0 0 20px 0; color: #1a1a2e; font-size: 24px;">{title}</h2>

        <p style="margin: 0 0 24px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            {message}
        </p>

        <div style="text-align: center; margin: 32px 0;">
            <a href="{APP_URL}" style="display: inline-block; background: linear-gradient(135deg, #d4af37 0%, #c9a227 100%); color: #1a1a2e; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px;">
                {t("notification_button")}
            </a>
        </div>

        <p style="margin: 24px 0 0 0; color: #6c757d; font-size: 13px; text-align: center;">
            {t("notification_footer")}
        </p>
        """

        return await self.send_email(
            to=to,
            subject=f"{title} - {APP_NAME}",
            html=self._base_template(content, language)
        )


# Instancia global
email_service = EmailService()
