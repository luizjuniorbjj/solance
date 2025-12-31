"""
AiSyster - Servico de Email
Usa Resend para envio de emails transacionais
"""

import httpx
from typing import Optional
from app.config import RESEND_API_KEY, EMAIL_FROM, EMAIL_REPLY_TO, APP_URL, APP_NAME


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

    def _base_template(self, content: str) -> str:
        """Template base para todos os emails"""
        # Logo via URL publica para melhor compatibilidade com clientes de email
        logo_url = f"{APP_URL}/static/icons/logo-email.png"
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
                                    <img src="{logo_url}" alt="AiSyster" style="width: 280px; height: auto; margin-bottom: 4px;">
                                    <p style="margin: 0; color: #d4af37; font-size: 14px; font-style: italic;">Sua companheira AI para apoio no dia a dia</p>
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
                                        Este email foi enviado por {APP_NAME}
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

    async def send_welcome_email(self, to: str, nome: str) -> bool:
        """Email de boas-vindas ao se registrar"""
        content = f"""
        <h2 style="margin: 0 0 20px 0; color: #1a1a2e; font-size: 24px;">Bem-vindo(a) ao AiSyster, {nome}!</h2>

        <p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Que alegria ter você conosco! O AiSyster foi criado para ser seu companheiro
            diário, um lugar seguro para conversar, refletir e crescer na fé.
        </p>

        <p style="margin: 0 0 24px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Estou aqui para ouvir, acolher e caminhar com você. Não importa o que esteja
            enfrentando - ansiedade, dúvidas, relacionamentos ou qualquer outra coisa -
            você não está sozinho(a).
        </p>

        <div style="text-align: center; margin: 32px 0;">
            <a href="{APP_URL}" style="display: inline-block; background: linear-gradient(135deg, #d4af37 0%, #c9a227 100%); color: #1a1a2e; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px;">
                Começar a Conversar
            </a>
        </div>

        <p style="margin: 24px 0 0 0; color: #6c757d; font-size: 14px; font-style: italic; text-align: center;">
            "Vinde a mim, todos os que estais cansados e sobrecarregados, e eu vos aliviarei." - Mateus 11:28
        </p>
        """

        return await self.send_email(
            to=to,
            subject=f"Bem-vindo(a) ao {APP_NAME}!",
            html=self._base_template(content)
        )

    async def send_password_reset_email(self, to: str, nome: str, reset_token: str) -> bool:
        """Email de recuperacao de senha"""
        reset_url = f"{APP_URL}?reset_token={reset_token}"

        content = f"""
        <h2 style="margin: 0 0 20px 0; color: #1a1a2e; font-size: 24px;">Recuperacao de Senha</h2>

        <p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Ola, {nome}!
        </p>

        <p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Recebemos uma solicitacao para redefinir sua senha. Se voce nao fez essa
            solicitacao, pode ignorar este email.
        </p>

        <p style="margin: 0 0 24px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Para criar uma nova senha, clique no botao abaixo:
        </p>

        <div style="text-align: center; margin: 32px 0;">
            <a href="{reset_url}" style="display: inline-block; background: linear-gradient(135deg, #d4af37 0%, #c9a227 100%); color: #1a1a2e; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px;">
                Redefinir Senha
            </a>
        </div>

        <p style="margin: 24px 0 0 0; color: #6c757d; font-size: 13px; text-align: center;">
            Este link expira em 1 hora. Se voce nao solicitou a recuperacao de senha,
            sua conta continua segura.
        </p>
        """

        return await self.send_email(
            to=to,
            subject=f"Recuperacao de Senha - {APP_NAME}",
            html=self._base_template(content)
        )

    async def send_subscription_confirmation(self, to: str, nome: str) -> bool:
        """Email de confirmacao de assinatura"""
        content = f"""
        <h2 style="margin: 0 0 20px 0; color: #1a1a2e; font-size: 24px;">Assinatura Confirmada!</h2>

        <p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Ola, {nome}!
        </p>

        <p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Obrigado por assinar o AiSyster Premium! Sua assinatura foi confirmada
            e voce agora tem acesso ilimitado ao seu companheiro espiritual.
        </p>

        <div style="background-color: #f8f9fa; border-radius: 8px; padding: 20px; margin: 24px 0;">
            <h3 style="margin: 0 0 12px 0; color: #1a1a2e; font-size: 16px;">O que voce ganhou:</h3>
            <ul style="margin: 0; padding-left: 20px; color: #4a4a4a; font-size: 14px; line-height: 1.8;">
                <li>Mensagens ilimitadas</li>
                <li>Companheiro sempre disponivel</li>
            </ul>
        </div>

        <div style="text-align: center; margin: 32px 0;">
            <a href="{APP_URL}" style="display: inline-block; background: linear-gradient(135deg, #d4af37 0%, #c9a227 100%); color: #1a1a2e; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px;">
                Continuar Conversando
            </a>
        </div>

        <p style="margin: 24px 0 0 0; color: #6c757d; font-size: 14px; font-style: italic; text-align: center;">
            Que Deus abencoe sua jornada!
        </p>
        """

        return await self.send_email(
            to=to,
            subject=f"Assinatura Confirmada - {APP_NAME} Premium",
            html=self._base_template(content)
        )

    async def send_subscription_renewal(self, to: str, nome: str) -> bool:
        """Email de renovacao de assinatura"""
        content = f"""
        <h2 style="margin: 0 0 20px 0; color: #1a1a2e; font-size: 24px;">Assinatura Renovada!</h2>

        <p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Ola, {nome}!
        </p>

        <p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Sua assinatura do AiSyster Premium foi renovada com sucesso.
            Continue aproveitando seu companheiro espiritual sem limites!
        </p>

        <div style="text-align: center; margin: 32px 0;">
            <a href="{APP_URL}" style="display: inline-block; background: linear-gradient(135deg, #d4af37 0%, #c9a227 100%); color: #1a1a2e; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px;">
                Ir para o AiSyster
            </a>
        </div>

        <p style="margin: 24px 0 0 0; color: #6c757d; font-size: 14px; text-align: center;">
            Obrigado por continuar conosco!
        </p>
        """

        return await self.send_email(
            to=to,
            subject=f"Assinatura Renovada - {APP_NAME}",
            html=self._base_template(content)
        )

    async def send_subscription_expiring(self, to: str, nome: str, days_left: int) -> bool:
        """Email de aviso de vencimento proximo"""
        content = f"""
        <h2 style="margin: 0 0 20px 0; color: #1a1a2e; font-size: 24px;">Sua assinatura vence em breve</h2>

        <p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Ola, {nome}!
        </p>

        <p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Sua assinatura do AiSyster Premium vence em <strong>{days_left} dias</strong>.
            Para continuar tendo acesso ilimitado ao seu companheiro espiritual,
            certifique-se de que seu metodo de pagamento esta atualizado.
        </p>

        <p style="margin: 0 0 24px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Se voce tem renovacao automatica ativada, nao precisa fazer nada -
            sua assinatura sera renovada automaticamente.
        </p>

        <div style="text-align: center; margin: 32px 0;">
            <a href="{APP_URL}" style="display: inline-block; background: linear-gradient(135deg, #d4af37 0%, #c9a227 100%); color: #1a1a2e; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px;">
                Verificar Assinatura
            </a>
        </div>
        """

        return await self.send_email(
            to=to,
            subject=f"Sua assinatura vence em {days_left} dias - {APP_NAME}",
            html=self._base_template(content)
        )

    async def send_subscription_cancelled(self, to: str, nome: str) -> bool:
        """Email de cancelamento de assinatura"""
        content = f"""
        <h2 style="margin: 0 0 20px 0; color: #1a1a2e; font-size: 24px;">Assinatura Cancelada</h2>

        <p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Ola, {nome}!
        </p>

        <p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Sua assinatura do AiSyster Premium foi cancelada. Voce ainda pode usar
            o AiSyster ate o final do periodo ja pago.
        </p>

        <p style="margin: 0 0 24px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Sentiremos sua falta! Se mudar de ideia, voce sempre pode voltar.
            Estaremos aqui esperando.
        </p>

        <div style="text-align: center; margin: 32px 0;">
            <a href="{APP_URL}" style="display: inline-block; background: linear-gradient(135deg, #d4af37 0%, #c9a227 100%); color: #1a1a2e; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px;">
                Reativar Assinatura
            </a>
        </div>

        <p style="margin: 24px 0 0 0; color: #6c757d; font-size: 14px; font-style: italic; text-align: center;">
            "Porque eu sei os planos que tenho para voces, diz o Senhor, planos de
            prosperidade e nao de calamidade, para dar-lhes um futuro e uma esperanca." - Jeremias 29:11
        </p>
        """

        return await self.send_email(
            to=to,
            subject=f"Assinatura Cancelada - {APP_NAME}",
            html=self._base_template(content)
        )

    async def send_notification_email(self, to: str, nome: str, title: str, message: str) -> bool:
        """Email de notificação/comunicado do AiSyster"""
        content = f"""
        <h2 style="margin: 0 0 20px 0; color: #1a1a2e; font-size: 24px;">{title}</h2>

        <p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Olá, {nome}!
        </p>

        <p style="margin: 0 0 24px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            {message}
        </p>

        <div style="text-align: center; margin: 32px 0;">
            <a href="{APP_URL}" style="display: inline-block; background: linear-gradient(135deg, #d4af37 0%, #c9a227 100%); color: #1a1a2e; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px;">
                Abrir AiSyster
            </a>
        </div>

        <p style="margin: 24px 0 0 0; color: #6c757d; font-size: 13px; text-align: center;">
            Você está recebendo este email porque tem notificações por email ativadas.
            <br>Para desativar, acesse Configurações no aplicativo.
        </p>
        """

        return await self.send_email(
            to=to,
            subject=f"{title} - {APP_NAME}",
            html=self._base_template(content)
        )


# Instancia global
email_service = EmailService()
