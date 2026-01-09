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
                    f"{self.base_url}/chat",
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
