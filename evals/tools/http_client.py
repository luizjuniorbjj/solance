"""
AiSyster Evals - HTTP Client
Cliente para chamar a API da AiSyster durante evals
"""

import httpx
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger("aisyster.evals.http")


@dataclass
class EvalResponse:
    """Resposta de uma chamada de eval"""
    success: bool
    response_text: str
    latency_ms: float
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class EvalHttpClient:
    """
    Cliente HTTP para chamar a API da AiSyster.

    Autentica como usuario de teste e envia mensagens ao chat.
    """

    def __init__(
        self,
        base_url: str,
        timeout_seconds: int = 60,
        retry_attempts: int = 2
    ):
        """
        Inicializa o cliente.

        Args:
            base_url: URL base da API (ex: http://localhost:8000)
            timeout_seconds: Timeout para requisicoes
            retry_attempts: Numero de tentativas em caso de falha
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout_seconds
        self.retry_attempts = retry_attempts
        self.token: Optional[str] = None
        self.client = httpx.Client(timeout=timeout_seconds)

    def authenticate(self, email: str, password: str) -> bool:
        """
        Autentica na API e armazena token.

        Args:
            email: Email do usuario de teste
            password: Senha do usuario de teste

        Returns:
            True se autenticacao bem sucedida
        """
        try:
            response = self.client.post(
                f"{self.base_url}/auth/login",
                json={"email": email, "password": password}
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token") or data.get("token")
                logger.info("Autenticacao bem sucedida")
                return True
            else:
                logger.error(f"Falha na autenticacao: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Erro na autenticacao: {e}")
            return False

    def send_message(self, message: str, conversation_id: Optional[str] = None) -> EvalResponse:
        """
        Envia mensagem ao chat e retorna resposta.

        Args:
            message: Mensagem a enviar
            conversation_id: ID da conversa (opcional, cria nova se None)

        Returns:
            EvalResponse com resultado
        """
        if not self.token:
            return EvalResponse(
                success=False,
                response_text="",
                latency_ms=0,
                error="Nao autenticado"
            )

        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {"message": message}

        if conversation_id:
            payload["conversation_id"] = conversation_id

        for attempt in range(self.retry_attempts + 1):
            try:
                import time
                start = time.time()

                response = self.client.post(
                    f"{self.base_url}/chat/",
                    json=payload,
                    headers=headers
                )

                latency_ms = (time.time() - start) * 1000

                if response.status_code == 200:
                    data = response.json()
                    return EvalResponse(
                        success=True,
                        response_text=data.get("response", data.get("message", "")),
                        latency_ms=latency_ms,
                        raw_response=data
                    )
                else:
                    if attempt < self.retry_attempts:
                        logger.warning(f"Tentativa {attempt + 1} falhou, retentando...")
                        continue

                    return EvalResponse(
                        success=False,
                        response_text="",
                        latency_ms=latency_ms,
                        error=f"HTTP {response.status_code}: {response.text}"
                    )

            except Exception as e:
                if attempt < self.retry_attempts:
                    logger.warning(f"Tentativa {attempt + 1} falhou com erro: {e}")
                    continue

                return EvalResponse(
                    success=False,
                    response_text="",
                    latency_ms=0,
                    error=str(e)
                )

        return EvalResponse(
            success=False,
            response_text="",
            latency_ms=0,
            error="Maximo de tentativas excedido"
        )

    def health_check(self) -> bool:
        """Verifica se a API esta disponivel."""
        try:
            response = self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception:
            return False

    def close(self):
        """Fecha o cliente HTTP."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class MockHttpClient:
    """
    Cliente HTTP mock para testar o sistema de evals sem API real.

    Simula respostas da AiSyster baseadas em padroes do input.
    """

    def __init__(self, **kwargs):
        """Inicializa o mock client (ignora parametros)."""
        import logging
        self.logger = logging.getLogger("aisyster.evals.http")
        self.token = "mock_token"
        self._response_templates = self._build_templates()

    def _build_templates(self) -> dict:
        """Constroi templates de resposta por categoria."""
        return {
            "theology": [
                "A Biblia nos ensina em Romanos 8:28 que todas as coisas cooperam para o bem daqueles que amam a Deus. Que voce encontre paz nessa verdade.",
                "Como diz Salmos 23:1, 'O Senhor e meu pastor, nada me faltara'. Confie no cuidado de Deus por voce.",
                "Jesus nos convida em Mateus 11:28: 'Vinde a mim, todos os que estais cansados e oprimidos, e eu vos aliviarei.'",
            ],
            "safety": [
                "Entendo que voce esta passando por um momento muito dificil. Quero que saiba que voce nao esta sozinho. Por favor, ligue para o CVV no 188 - eles estao disponiveis 24 horas e podem ajudar. Sua vida tem valor.",
                "O que voce esta sentindo e muito serio e voce merece apoio profissional. Ligue agora para o CVV: 188. Eles podem ouvir e ajudar. Voce importa.",
                "Estou preocupado com voce. Por favor, busque ajuda profissional. O CVV (188) esta disponivel 24h. Tambem recomendo conversar com um psicologo ou psiquiatra. Voce nao precisa enfrentar isso sozinho.",
            ],
            "finance": [
                "Cuidado com promessas de prosperidade financeira em troca de ofertas. A Biblia nos alerta contra falsos ensinamentos. Deus nao negocia bencaos por dinheiro.",
                "Nenhum lider religioso deve pedir seu dinheiro em nome de Deus. Isso nao e biblico. Proteja suas financas e busque orientacao de pessoas de confianca.",
                "A verdadeira fe nao exige pagamento. Desconfie de quem pede dinheiro prometendo bencaos divinas. Isso e manipulacao.",
            ],
            "reliability": [
                "Fico feliz em poder conversar com voce. Como posso ajudar hoje?",
                "Estou aqui para ouvir e oferecer apoio pastoral. O que esta em seu coracao?",
                "Obrigada por compartilhar comigo. Vamos conversar sobre isso.",
            ],
            "product": [
                "Posso ajudar voce a usar melhor o aplicativo. O que gostaria de saber?",
                "Para cancelar sua conta, va em Configuracoes > Conta > Cancelar. Respeitamos sua decisao.",
                "Suas informacoes sao protegidas conforme a LGPD. Nao vendemos dados para terceiros.",
            ],
        }

    def authenticate(self, email: str, password: str) -> bool:
        """Mock: sempre autentica com sucesso."""
        self.logger.info(f"[MOCK] Autenticacao simulada para {email}")
        return True

    def send_message(self, message: str, conversation_id=None) -> "EvalResponse":
        """Simula resposta da AiSyster baseada no conteudo da mensagem."""
        import time
        import random

        start = time.time()
        message_lower = message.lower()

        if any(word in message_lower for word in ["suicid", "morrer", "me matar", "cortar", "acabar com tudo", "nao aguento"]):
            category = "safety"
        elif any(word in message_lower for word in ["oferta", "dizimo", "semente", "dinheiro", "prosperidade", "deus mandou"]):
            category = "finance"
        elif any(word in message_lower for word in ["biblia", "deus", "jesus", "oracao", "fe", "pecado", "perdao", "salmo"]):
            category = "theology"
        elif any(word in message_lower for word in ["app", "funciona", "cancelar", "conta", "dados", "bug"]):
            category = "product"
        else:
            category = "reliability"

        templates = self._response_templates.get(category, self._response_templates["reliability"])
        response_text = random.choice(templates)

        time.sleep(random.uniform(0.1, 0.3))
        latency_ms = (time.time() - start) * 1000

        self.logger.debug(f"[MOCK] Categoria detectada: {category}")

        return EvalResponse(
            success=True,
            response_text=response_text,
            latency_ms=latency_ms,
            raw_response={"mock": True, "category": category}
        )

    def health_check(self) -> bool:
        return True

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
