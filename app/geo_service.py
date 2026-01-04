"""
AiSyster - Servico de Geolocalizacao
Detecta pais/regiao do usuario pelo IP ou headers do request
"""

import httpx
from typing import Optional, Dict
from functools import lru_cache
import asyncio

# Cache de localizacoes por IP (evita chamadas repetidas)
_location_cache: Dict[str, str] = {}


async def get_location_from_ip(ip_address: str) -> Optional[str]:
    """
    Detecta pais/regiao pelo IP usando API gratuita.
    Retorna string como "Brasil" ou "Estados Unidos".
    """
    # Ignorar IPs locais
    if ip_address in ["127.0.0.1", "localhost", "::1"] or ip_address.startswith("192.168."):
        return None

    # Verificar cache
    if ip_address in _location_cache:
        return _location_cache[ip_address]

    try:
        # Usar ip-api.com (gratuito, 45 req/min)
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(
                f"http://ip-api.com/json/{ip_address}?fields=status,country,countryCode"
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    country = data.get("country", "")
                    # Cachear resultado
                    _location_cache[ip_address] = country
                    # Limitar tamanho do cache
                    if len(_location_cache) > 1000:
                        # Remover metade mais antiga
                        keys_to_remove = list(_location_cache.keys())[:500]
                        for key in keys_to_remove:
                            del _location_cache[key]
                    return country

    except Exception as e:
        print(f"[GEO] Error getting location for IP {ip_address}: {e}")

    return None


def get_location_from_headers(headers: dict) -> Optional[str]:
    """
    Detecta localizacao pelos headers do request.
    Funciona com CloudFlare, Railway e outros proxies.
    """
    # CloudFlare headers
    cf_country = headers.get("cf-ipcountry")
    if cf_country:
        return country_code_to_name(cf_country)

    # Vercel/Next.js
    vercel_country = headers.get("x-vercel-ip-country")
    if vercel_country:
        return country_code_to_name(vercel_country)

    # Detectar pelo Accept-Language (fallback)
    accept_lang = headers.get("accept-language", "")
    if accept_lang:
        # Exemplos: "pt-BR,pt;q=0.9,en-US;q=0.8"
        if "pt-BR" in accept_lang or "pt-br" in accept_lang:
            return "Brasil"
        elif "en-US" in accept_lang or "en-us" in accept_lang:
            return "Estados Unidos"
        elif "es-" in accept_lang.lower():
            return "Espanha"  # ou pais hispanico

    return None


def country_code_to_name(code: str) -> str:
    """Converte codigo ISO do pais para nome em portugues."""
    COUNTRY_NAMES = {
        "BR": "Brasil",
        "US": "Estados Unidos",
        "PT": "Portugal",
        "AO": "Angola",
        "MZ": "Mocambique",
        "CV": "Cabo Verde",
        "GW": "Guine-Bissau",
        "ST": "Sao Tome e Principe",
        "TL": "Timor-Leste",
        "ES": "Espanha",
        "FR": "Franca",
        "DE": "Alemanha",
        "IT": "Italia",
        "GB": "Reino Unido",
        "JP": "Japao",
        "CN": "China",
        "AR": "Argentina",
        "CL": "Chile",
        "CO": "Colombia",
        "MX": "Mexico",
        "PE": "Peru",
        "VE": "Venezuela",
        "UY": "Uruguai",
        "PY": "Paraguai",
        "CA": "Canada",
        "AU": "Australia",
    }
    return COUNTRY_NAMES.get(code.upper(), code)


async def detect_user_location(
    ip_address: Optional[str] = None,
    headers: Optional[dict] = None
) -> Optional[str]:
    """
    Detecta localizacao do usuario usando multiplas fontes:
    1. Headers do proxy (CloudFlare, etc) - mais rapido
    2. API de geolocalizacao por IP - mais preciso

    Retorna: Nome do pais em portugues ou None
    """
    # 1. Tentar pelos headers primeiro (instantaneo)
    if headers:
        location = get_location_from_headers(headers)
        if location:
            return location

    # 2. Tentar por IP (requer chamada externa)
    if ip_address:
        location = await get_location_from_ip(ip_address)
        if location:
            return location

    return None
