"""
AiSyster - Servico OpenAI
Speech-to-Text (Whisper) e Text-to-Speech
"""

import io
from typing import Optional
from openai import OpenAI

from app.config import OPENAI_API_KEY


class OpenAIService:
    """
    Servico para STT (Whisper) e TTS da OpenAI
    """

    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY nao configurada")
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    async def speech_to_text(self, audio_data: bytes, filename: str = "audio.webm") -> str:
        """
        Converte audio em texto usando Whisper

        Args:
            audio_data: Bytes do arquivo de audio
            filename: Nome do arquivo (importante para detectar formato)

        Returns:
            Texto transcrito
        """
        # Criar arquivo em memoria
        audio_file = io.BytesIO(audio_data)
        audio_file.name = filename

        # Chamar Whisper API
        transcription = self.client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="pt"  # Portugues brasileiro
        )

        return transcription.text

    async def text_to_speech(
        self,
        text: str,
        voice: str = "nova",  # nova = voz feminina natural
        speed: float = 1.0
    ) -> bytes:
        """
        Converte texto em audio usando TTS

        Args:
            text: Texto para converter em fala
            voice: Voz a usar (alloy, echo, fable, onyx, nova, shimmer)
            speed: Velocidade (0.25 a 4.0)

        Returns:
            Bytes do arquivo MP3
        """
        response = self.client.audio.speech.create(
            model="tts-1",  # tts-1 = mais rapido, tts-1-hd = mais qualidade
            voice=voice,
            input=text,
            speed=speed
        )

        # Retornar bytes do audio
        return response.content

    async def transcribe_and_respond(
        self,
        audio_data: bytes,
        filename: str = "audio.webm"
    ) -> dict:
        """
        Conveniencia: transcreve audio e retorna texto
        (A resposta da IA sera feita pelo ai_service.py)

        Returns:
            {"text": "texto transcrito", "success": True}
        """
        try:
            text = await self.speech_to_text(audio_data, filename)
            return {
                "text": text,
                "success": True
            }
        except Exception as e:
            return {
                "text": "",
                "success": False,
                "error": str(e)
            }


# Instancia global (lazy loading)
_openai_service: Optional[OpenAIService] = None


def get_openai_service() -> OpenAIService:
    """
    Retorna instancia do servico OpenAI (singleton)
    """
    global _openai_service
    if _openai_service is None:
        _openai_service = OpenAIService()
    return _openai_service
