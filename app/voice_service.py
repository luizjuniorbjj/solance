"""
SoulHaven - Serviço de Voz
STT (Speech-to-Text) via Whisper e TTS (Text-to-Speech) via OpenAI
"""

import io
import tempfile
import os
from typing import Optional, Tuple
from pathlib import Path

from openai import OpenAI

from app.config import (
    OPENAI_API_KEY,
    VOICE_ENABLED,
    STT_MODEL,
    STT_MAX_FILE_SIZE,
    TTS_MODEL,
    TTS_VOICE,
    TTS_SPEED
)


class VoiceService:
    """
    Serviço de voz para AiSyster
    - STT: Converte áudio do usuário em texto (Whisper)
    - TTS: Converte resposta da AiSyster em áudio (OpenAI TTS)
    """

    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.enabled = VOICE_ENABLED and bool(OPENAI_API_KEY)

    async def speech_to_text(
        self,
        audio_bytes: bytes,
        filename: str = "audio.webm",
        language: str = "pt"
    ) -> Tuple[bool, str]:
        """
        Converte áudio em texto usando Whisper.

        Args:
            audio_bytes: Bytes do arquivo de áudio
            filename: Nome do arquivo (para detectar formato)
            language: Idioma do áudio (pt = português)

        Returns:
            Tuple[bool, str]: (sucesso, texto_transcrito ou mensagem_erro)
        """
        if not self.enabled:
            return False, "Serviço de voz desabilitado"

        # Validar tamanho
        if len(audio_bytes) > STT_MAX_FILE_SIZE:
            return False, f"Áudio muito grande. Máximo {STT_MAX_FILE_SIZE // (1024*1024)}MB"

        if len(audio_bytes) < 100:
            return False, "Áudio muito curto ou vazio"

        try:
            # Criar arquivo temporário com a extensão correta
            suffix = Path(filename).suffix or ".webm"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            try:
                # Chamar Whisper
                with open(tmp_path, "rb") as audio_file:
                    transcript = self.client.audio.transcriptions.create(
                        model=STT_MODEL,
                        file=audio_file,
                        language=language,
                        response_format="text"
                    )

                # Limpar texto
                text = transcript.strip() if isinstance(transcript, str) else str(transcript).strip()

                if not text:
                    return False, "Não consegui entender o áudio. Tente falar mais claramente."

                print(f"[STT] Transcrito: {text[:100]}...")
                return True, text

            finally:
                # Limpar arquivo temporário
                try:
                    os.unlink(tmp_path)
                except:
                    pass

        except Exception as e:
            print(f"[STT] Erro: {e}")
            return False, f"Erro ao transcrever: {str(e)}"

    async def text_to_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None
    ) -> Tuple[bool, bytes, str]:
        """
        Converte texto em áudio usando OpenAI TTS.

        Args:
            text: Texto para converter em áudio
            voice: Voz a usar (opcional, usa padrão se não informado)
            speed: Velocidade (0.25 a 4.0)

        Returns:
            Tuple[bool, bytes, str]: (sucesso, audio_bytes, mensagem_erro)
        """
        if not self.enabled:
            return False, b"", "Serviço de voz desabilitado"

        if not text or len(text.strip()) == 0:
            return False, b"", "Texto vazio"

        # Limitar tamanho do texto (TTS tem limite de ~4096 chars)
        max_chars = 4000
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
            print(f"[TTS] Texto truncado para {max_chars} caracteres")

        try:
            response = self.client.audio.speech.create(
                model=TTS_MODEL,
                voice=voice or TTS_VOICE,
                input=text,
                speed=speed or TTS_SPEED,
                response_format="mp3"  # MP3 é mais compatível
            )

            # Ler bytes do áudio
            audio_bytes = response.content

            print(f"[TTS] Gerado áudio de {len(audio_bytes)} bytes")
            return True, audio_bytes, ""

        except Exception as e:
            print(f"[TTS] Erro: {e}")
            return False, b"", f"Erro ao gerar áudio: {str(e)}"

    async def chat_with_voice(
        self,
        audio_bytes: bytes,
        filename: str,
        chat_callback,
        user_id: str,
        conversation_id: Optional[str] = None,
        return_audio: bool = True
    ) -> dict:
        """
        Fluxo completo: Áudio do usuário -> Texto -> Chat -> Áudio da resposta

        Args:
            audio_bytes: Áudio do usuário
            filename: Nome do arquivo de áudio
            chat_callback: Função assíncrona de chat (ai_service.chat)
            user_id: ID do usuário
            conversation_id: ID da conversa (opcional)
            return_audio: Se deve retornar áudio da resposta

        Returns:
            dict com: success, user_text, response_text, response_audio, conversation_id
        """
        result = {
            "success": False,
            "user_text": "",
            "response_text": "",
            "response_audio": None,
            "conversation_id": conversation_id,
            "error": ""
        }

        # 1. Transcrever áudio do usuário
        stt_success, user_text = await self.speech_to_text(audio_bytes, filename)

        if not stt_success:
            result["error"] = user_text  # Mensagem de erro
            return result

        result["user_text"] = user_text

        # 2. Processar no chat (com instrução para resposta curta - modo voz)
        # Adicionar prefixo invisível para forçar resposta concisa
        voice_instruction = "[MODO VOZ - Responda em 1-2 frases curtas e diretas. Seja objetiva.]\n"
        try:
            chat_result = await chat_callback(
                user_id=user_id,
                message=voice_instruction + user_text,
                conversation_id=conversation_id
            )
            result["response_text"] = chat_result["response"]
            result["conversation_id"] = chat_result["conversation_id"]
        except Exception as e:
            result["error"] = f"Erro no chat: {str(e)}"
            return result

        # 3. Converter resposta em áudio (se solicitado)
        if return_audio and result["response_text"]:
            tts_success, audio, tts_error = await self.text_to_speech(result["response_text"])
            if tts_success:
                result["response_audio"] = audio
            else:
                print(f"[VOICE] TTS falhou: {tts_error}")
                # Não falhar a requisição por causa do TTS

        result["success"] = True
        return result

    def get_available_voices(self) -> list:
        """
        Retorna as vozes disponíveis para TTS.
        """
        return [
            {"id": "alloy", "name": "Alloy", "description": "Neutra, versátil"},
            {"id": "echo", "name": "Echo", "description": "Masculina, grave"},
            {"id": "fable", "name": "Fable", "description": "Expressiva, narrativa"},
            {"id": "onyx", "name": "Onyx", "description": "Masculina, profunda"},
            {"id": "nova", "name": "Nova", "description": "Feminina, suave (padrão AiSyster)"},
            {"id": "shimmer", "name": "Shimmer", "description": "Feminina, brilhante"},
        ]


# Instância global para reutilização
voice_service = VoiceService()
