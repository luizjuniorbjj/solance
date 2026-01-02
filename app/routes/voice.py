"""
AiSyster - Rotas de Voz
Speech-to-Text e Text-to-Speech
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from pydantic import BaseModel

from app.auth import get_current_user
from app.database import get_db, Database
from app.ai_service import AIService
from app.openai_service import get_openai_service
from app.security import rate_limiter
from app.config import FREE_MESSAGE_LIMIT, FREE_WARNING_AT, FREE_URGENT_AT

router = APIRouter(prefix="/voice", tags=["Voice"])


# ============================================
# MODELOS
# ============================================

class VoiceChatResponse(BaseModel):
    text_response: str  # Resposta em texto da AiSyster
    conversation_id: str
    model_used: str
    tokens_used: int
    transcribed_text: str  # O que o usuario disse
    messages_used: Optional[int] = None
    messages_limit: Optional[int] = None
    limit_warning: Optional[str] = None


class TTSRequest(BaseModel):
    text: str
    voice: str = "nova"  # nova = feminina natural
    speed: float = 1.0


# ============================================
# ROTAS
# ============================================

@router.post("/chat", response_model=VoiceChatResponse)
async def voice_chat(
    audio: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Chat por voz: recebe audio, transcreve, processa com IA e retorna resposta.
    O frontend pode chamar /voice/tts para converter a resposta em audio.
    """
    user_id = current_user["user_id"]

    # Rate limiting
    if not rate_limiter.is_allowed(user_id, max_requests=20, window_seconds=60):
        raise HTTPException(
            status_code=429,
            detail="Muitas mensagens de voz. Aguarde um momento."
        )

    # Validar tipo de audio
    allowed_types = [
        "audio/webm", "audio/mp3", "audio/mpeg", "audio/wav",
        "audio/ogg", "audio/m4a", "audio/mp4", "audio/x-m4a"
    ]
    if audio.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Formato de audio nao suportado: {audio.content_type}"
        )

    # Ler audio
    audio_bytes = await audio.read()

    # Limite de tamanho (25MB - limite do Whisper)
    if len(audio_bytes) > 25 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="Audio muito grande. Maximo 25MB."
        )

    # Transcrever audio
    try:
        openai_service = get_openai_service()
        transcription = await openai_service.speech_to_text(
            audio_bytes,
            filename=audio.filename or "audio.webm"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao transcrever audio: {str(e)}"
        )

    if not transcription.strip():
        raise HTTPException(
            status_code=400,
            detail="Nao foi possivel entender o audio. Tente falar mais claramente."
        )

    # Buscar usuario e verificar limites
    user = await db.get_user_by_id(user_id)
    is_premium = user.get("is_premium", False)
    messages_used = user.get("trial_messages_used", 0)

    # Verificar limite para usuarios free
    limit_warning = None
    if not is_premium:
        if messages_used >= FREE_MESSAGE_LIMIT:
            raise HTTPException(
                status_code=402,
                detail="Voce atingiu o limite gratuito. Assine para continuar!"
            )

    # Processar com IA (usando texto transcrito)
    ai_service = AIService(db)
    try:
        result = await ai_service.chat(
            user_id=user_id,
            message=transcription,
            conversation_id=conversation_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar mensagem: {str(e)}"
        )

    # Calcular aviso de limite
    if not is_premium:
        messages_used += 1
        if messages_used >= FREE_MESSAGE_LIMIT:
            limit_warning = "reached"
        elif messages_used >= FREE_URGENT_AT:
            limit_warning = "urgent"
        elif messages_used >= FREE_WARNING_AT:
            limit_warning = "soft"

    # Log de auditoria
    await db.log_audit(
        user_id=user_id,
        action="voice_chat_sent",
        details={"conversation_id": result["conversation_id"]}
    )

    return VoiceChatResponse(
        text_response=result["response"],
        conversation_id=result["conversation_id"],
        model_used=result["model_used"],
        tokens_used=result["tokens_used"],
        transcribed_text=transcription,
        messages_used=messages_used if not is_premium else None,
        messages_limit=FREE_MESSAGE_LIMIT if not is_premium else None,
        limit_warning=limit_warning
    )


@router.post("/tts")
async def text_to_speech(
    request: TTSRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Converte texto em audio (TTS).
    Retorna arquivo MP3.
    """
    user_id = current_user["user_id"]

    # Rate limiting (TTS e mais leve)
    if not rate_limiter.is_allowed(f"tts_{user_id}", max_requests=30, window_seconds=60):
        raise HTTPException(
            status_code=429,
            detail="Muitas requisicoes de audio. Aguarde um momento."
        )

    # Validar texto
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Texto vazio")

    if len(request.text) > 4096:
        raise HTTPException(
            status_code=400,
            detail="Texto muito longo. Maximo 4096 caracteres."
        )

    # Gerar audio
    try:
        openai_service = get_openai_service()
        audio_bytes = await openai_service.text_to_speech(
            text=request.text,
            voice=request.voice,
            speed=request.speed
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar audio: {str(e)}"
        )

    # Retornar MP3
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline; filename=response.mp3"
        }
    )


@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Apenas transcreve audio para texto (sem processar com IA).
    Util para previsualizar o que foi dito.
    """
    user_id = current_user["user_id"]

    # Rate limiting
    if not rate_limiter.is_allowed(f"transcribe_{user_id}", max_requests=30, window_seconds=60):
        raise HTTPException(
            status_code=429,
            detail="Muitas transcricoes. Aguarde um momento."
        )

    # Ler audio
    audio_bytes = await audio.read()

    # Transcrever
    try:
        openai_service = get_openai_service()
        text = await openai_service.speech_to_text(
            audio_bytes,
            filename=audio.filename or "audio.webm"
        )
        return {"text": text, "success": True}
    except Exception as e:
        return {"text": "", "success": False, "error": str(e)}
