"""
AiSyster - Rotas de Voz
STT (Speech-to-Text) e TTS (Text-to-Speech)
"""

import base64
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from pydantic import BaseModel

from app.auth import get_current_user
from app.database import get_db, Database
from app.ai_service import AIService
from app.voice_service import voice_service
from app.security import rate_limiter
from app.config import VOICE_ENABLED, FREE_MESSAGE_LIMIT

router = APIRouter(prefix="/voice", tags=["Voice"])


# ============================================
# MODELOS
# ============================================

class TTSRequest(BaseModel):
    """Requisição para Text-to-Speech"""
    text: str
    voice: Optional[str] = None  # alloy, echo, fable, onyx, nova, shimmer
    speed: Optional[float] = None  # 0.25 a 4.0


class STTResponse(BaseModel):
    """Resposta de Speech-to-Text"""
    success: bool
    text: str
    error: Optional[str] = None


class VoiceChatResponse(BaseModel):
    """Resposta de chat por voz"""
    success: bool
    user_text: str
    response_text: str
    response_audio_base64: Optional[str] = None
    conversation_id: str
    error: Optional[str] = None


class VoicesResponse(BaseModel):
    """Lista de vozes disponíveis"""
    voices: list


# ============================================
# ROTAS
# ============================================

@router.get("/status")
async def voice_status():
    """
    Verifica se o serviço de voz está disponível
    """
    return {
        "enabled": VOICE_ENABLED and voice_service.enabled,
        "stt_available": voice_service.enabled,
        "tts_available": voice_service.enabled
    }


@router.get("/voices", response_model=VoicesResponse)
async def get_voices():
    """
    Lista as vozes disponíveis para TTS
    """
    return VoicesResponse(voices=voice_service.get_available_voices())


@router.post("/stt", response_model=STTResponse)
async def speech_to_text(
    audio: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Converte áudio em texto (Speech-to-Text)

    Formatos suportados: mp3, mp4, mpeg, mpga, m4a, wav, webm
    Tamanho máximo: 25MB
    """
    user_id = current_user["user_id"]

    if not voice_service.enabled:
        raise HTTPException(status_code=503, detail="Serviço de voz indisponível")

    # Rate limiting
    if not rate_limiter.is_allowed(user_id, max_requests=20, window_seconds=60):
        raise HTTPException(status_code=429, detail="Muitas requisições. Aguarde um momento.")

    # Ler arquivo
    audio_bytes = await audio.read()

    # Transcrever
    success, result = await voice_service.speech_to_text(
        audio_bytes=audio_bytes,
        filename=audio.filename or "audio.webm"
    )

    if success:
        return STTResponse(success=True, text=result)
    else:
        return STTResponse(success=False, text="", error=result)


@router.post("/tts")
async def text_to_speech(
    request: TTSRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Converte texto em áudio (Text-to-Speech)

    Retorna arquivo MP3
    """
    user_id = current_user["user_id"]

    if not voice_service.enabled:
        raise HTTPException(status_code=503, detail="Serviço de voz indisponível")

    # Rate limiting
    if not rate_limiter.is_allowed(user_id, max_requests=20, window_seconds=60):
        raise HTTPException(status_code=429, detail="Muitas requisições. Aguarde um momento.")

    # Gerar áudio
    success, audio_bytes, error = await voice_service.text_to_speech(
        text=request.text,
        voice=request.voice,
        speed=request.speed
    )

    if not success:
        raise HTTPException(status_code=500, detail=error)

    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "attachment; filename=aisyster_response.mp3"
        }
    )


@router.post("/chat", response_model=VoiceChatResponse)
async def voice_chat(
    audio: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    return_audio: bool = Form(True),
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Chat completo por voz:
    1. Recebe áudio do usuário
    2. Transcreve para texto
    3. Processa no chat da AiSyster
    4. Converte resposta em áudio
    5. Retorna texto + áudio

    Formatos de áudio suportados: mp3, mp4, mpeg, mpga, m4a, wav, webm
    """
    user_id = current_user["user_id"]

    if not voice_service.enabled:
        raise HTTPException(status_code=503, detail="Serviço de voz indisponível")

    # Rate limiting (mais restritivo para voice chat)
    if not rate_limiter.is_allowed(user_id, max_requests=15, window_seconds=60):
        raise HTTPException(status_code=429, detail="Muitas mensagens. Aguarde um momento.")

    # Verificar limite de mensagens para usuários free
    user = await db.get_user_by_id(user_id)
    is_premium = user.get("is_premium", False)
    messages_used = user.get("trial_messages_used", 0)

    if not is_premium and messages_used >= FREE_MESSAGE_LIMIT:
        raise HTTPException(
            status_code=402,
            detail="Você atingiu o limite gratuito. Assine para continuar conversando!"
        )

    # Obter preferências de idioma/voz do perfil do usuário
    profile = await db.get_user_profile(user_id)
    user_language = profile.get("language", "auto") if profile else "auto"
    spoken_language = profile.get("spoken_language", "auto") if profile else "auto"
    user_voice = profile.get("voice", "nova") if profile else "nova"

    # Ler áudio
    audio_bytes = await audio.read()

    # Criar AI service
    ai_service = AIService(db)

    # Processar voz completo
    result = await voice_service.chat_with_voice(
        audio_bytes=audio_bytes,
        filename=audio.filename or "audio.webm",
        chat_callback=ai_service.chat,
        user_id=user_id,
        conversation_id=conversation_id,
        return_audio=return_audio,
        language=user_language,
        spoken_language=spoken_language,
        voice=user_voice
    )

    if not result["success"]:
        return VoiceChatResponse(
            success=False,
            user_text=result.get("user_text", ""),
            response_text="",
            conversation_id=conversation_id or "",
            error=result.get("error", "Erro desconhecido")
        )

    # Converter áudio para base64 se disponível
    audio_base64 = None
    if result.get("response_audio"):
        audio_base64 = base64.b64encode(result["response_audio"]).decode("utf-8")

    # Log de auditoria
    await db.log_audit(
        user_id=user_id,
        action="voice_chat",
        details={
            "conversation_id": result["conversation_id"],
            "user_text_length": len(result["user_text"]),
            "response_text_length": len(result["response_text"]),
            "audio_returned": audio_base64 is not None
        }
    )

    return VoiceChatResponse(
        success=True,
        user_text=result["user_text"],
        response_text=result["response_text"],
        response_audio_base64=audio_base64,
        conversation_id=result["conversation_id"]
    )


@router.post("/chat-audio-response")
async def voice_chat_audio_response(
    audio: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Chat por voz que retorna o áudio diretamente (sem base64)

    Útil para players de áudio nativos
    """
    user_id = current_user["user_id"]

    if not voice_service.enabled:
        raise HTTPException(status_code=503, detail="Serviço de voz indisponível")

    # Rate limiting
    if not rate_limiter.is_allowed(user_id, max_requests=15, window_seconds=60):
        raise HTTPException(status_code=429, detail="Muitas mensagens. Aguarde um momento.")

    # Verificar limite
    user = await db.get_user_by_id(user_id)
    is_premium = user.get("is_premium", False)
    messages_used = user.get("trial_messages_used", 0)

    if not is_premium and messages_used >= FREE_MESSAGE_LIMIT:
        raise HTTPException(status_code=402, detail="Limite gratuito atingido")

    # Obter preferências de idioma/voz do perfil do usuário
    profile = await db.get_user_profile(user_id)
    user_language = profile.get("language", "auto") if profile else "auto"
    spoken_language = profile.get("spoken_language", "auto") if profile else "auto"
    user_voice = profile.get("voice", "nova") if profile else "nova"

    # Ler áudio
    audio_bytes = await audio.read()

    # Criar AI service
    ai_service = AIService(db)

    # Processar
    result = await voice_service.chat_with_voice(
        audio_bytes=audio_bytes,
        filename=audio.filename or "audio.webm",
        chat_callback=ai_service.chat,
        user_id=user_id,
        conversation_id=conversation_id,
        return_audio=True,
        language=user_language,
        spoken_language=spoken_language,
        voice=user_voice
    )

    if not result["success"] or not result.get("response_audio"):
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Erro ao processar áudio")
        )

    # Retornar áudio direto
    return Response(
        content=result["response_audio"],
        media_type="audio/mpeg",
        headers={
            "X-User-Text": result["user_text"][:200],  # Primeiros 200 chars
            "X-Conversation-Id": result["conversation_id"],
            "Content-Disposition": "inline; filename=aisyster_response.mp3"
        }
    )
