"""
SoulHaven - Segurança e Criptografia
Sistema de autenticação e proteção de dados sensíveis
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from base64 import b64encode, b64decode

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import bcrypt
import jwt

from app.config import SECRET_KEY, ENCRYPTION_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_HOURS, JWT_REFRESH_TOKEN_DAYS


# ============================================
# PASSWORD HASHING
# ============================================

def hash_password(password: str) -> str:
    """
    Hash de senha usando bcrypt
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """
    Verifica se a senha corresponde ao hash
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


# ============================================
# JWT TOKENS
# ============================================

def create_access_token(user_id: str, email: str) -> str:
    """
    Cria token JWT para autenticação (curta duração - 1h)
    """
    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=JWT_ACCESS_TOKEN_HOURS),
        "type": "access"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """
    Cria refresh token para renovação (longa duração - 30 dias)
    """
    payload = {
        "sub": str(user_id),
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(days=JWT_REFRESH_TOKEN_DAYS),
        "type": "refresh"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    """
    Verifica e decodifica token JWT
    Retorna payload se válido, None se inválido
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ============================================
# DATA ENCRYPTION (Fernet - AES 128)
# ============================================

def _get_fernet_key(user_salt: str = "") -> bytes:
    """
    Deriva uma chave Fernet a partir da chave mestra + salt do usuário
    Isso garante que cada usuário tem criptografia única
    """
    combined = f"{ENCRYPTION_KEY}{user_salt}".encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"soulhaven_salt_v1",  # Salt fixo para derivação
        iterations=100000,
    )
    key = b64encode(kdf.derive(combined))
    return key


def encrypt_data(data: str, user_id: str = "") -> bytes:
    """
    Criptografa dados sensíveis
    Usa o user_id como salt para chave única por usuário
    """
    if not data:
        return b""

    key = _get_fernet_key(user_id)
    fernet = Fernet(key)
    encrypted = fernet.encrypt(data.encode('utf-8'))
    return encrypted


def decrypt_data(encrypted_data: bytes, user_id: str = "") -> str:
    """
    Descriptografa dados sensíveis
    """
    if not encrypted_data:
        return ""

    try:
        key = _get_fernet_key(user_id)
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted_data)
        return decrypted.decode('utf-8')
    except Exception as e:
        print(f"[DECRYPT_ERROR] Failed to decrypt for user {user_id[:8] if user_id else 'N/A'}...: {type(e).__name__}")
        return "[Mensagem não pôde ser recuperada]"  # Mostrar erro ao usuário


# ============================================
# UTILITY FUNCTIONS
# ============================================

def generate_secure_token(length: int = 32) -> str:
    """
    Gera token seguro para reset de senha, etc.
    """
    return secrets.token_urlsafe(length)


def hash_for_audit(data: str) -> str:
    """
    Hash one-way para logs de auditoria (não reversível)
    Útil para logar ações sem expor dados sensíveis
    """
    return hashlib.sha256(data.encode()).hexdigest()[:16]


# ============================================
# RATE LIMITING
# ============================================

class RateLimiter:
    """
    Rate limiting em memória (para produção, usar Redis)
    """
    def __init__(self):
        self._requests = {}

    def is_allowed(self, user_id: str, max_requests: int = 60, window_seconds: int = 60) -> bool:
        """
        Verifica se usuário pode fazer mais requests
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)

        if user_id not in self._requests:
            self._requests[user_id] = []

        # Remove requests antigos
        self._requests[user_id] = [
            req_time for req_time in self._requests[user_id]
            if req_time > window_start
        ]

        # Verifica limite
        if len(self._requests[user_id]) >= max_requests:
            return False

        # Registra request
        self._requests[user_id].append(now)
        return True

    def get_remaining(self, user_id: str, max_requests: int = 60, window_seconds: int = 60) -> int:
        """
        Retorna quantos requests restam
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)

        if user_id not in self._requests:
            return max_requests

        recent = [
            req_time for req_time in self._requests[user_id]
            if req_time > window_start
        ]

        return max(0, max_requests - len(recent))


# Instância global do rate limiter
rate_limiter = RateLimiter()
