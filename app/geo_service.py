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
    1. Headers de proxy (CloudFlare, Railway) - mais confiavel
    2. API de geolocalizacao por IP - preciso
    3. Accept-Language - ultimo recurso (menos confiavel)

    Retorna: Nome do pais em portugues ou None
    """
    # Normalizar headers para lowercase (FastAPI pode enviar mixed case)
    if headers:
        headers = {k.lower(): v for k, v in headers.items()}

    print(f"[GEO] Iniciando deteccao - IP: {ip_address}")

    # 1. Tentar headers de proxy primeiro (CloudFlare, Railway, Vercel)
    if headers:
        # CloudFlare
        cf_country = headers.get("cf-ipcountry")
        if cf_country:
            location = country_code_to_name(cf_country)
            print(f"[GEO] Detectado via CloudFlare: {location}")
            return location

        # Vercel
        vercel_country = headers.get("x-vercel-ip-country")
        if vercel_country:
            location = country_code_to_name(vercel_country)
            print(f"[GEO] Detectado via Vercel: {location}")
            return location

        # Railway usa X-Forwarded-For para o IP real
        x_forwarded = headers.get("x-forwarded-for")
        if x_forwarded:
            # Pegar o primeiro IP (cliente original)
            real_ip = x_forwarded.split(",")[0].strip()
            print(f"[GEO] X-Forwarded-For encontrado: {x_forwarded} -> IP real: {real_ip}")
            if real_ip and real_ip != ip_address:
                ip_address = real_ip

        x_real_ip = headers.get("x-real-ip")
        if x_real_ip and x_real_ip != ip_address:
            print(f"[GEO] IP real via X-Real-IP: {x_real_ip}")
            ip_address = x_real_ip

    # 2. Tentar por IP (API externa - mais preciso que Accept-Language)
    if ip_address:
        # Ignorar IPs privados/internos do Railway
        if not (ip_address.startswith("10.") or ip_address.startswith("172.") or ip_address.startswith("192.168.")):
            location = await get_location_from_ip(ip_address)
            if location:
                print(f"[GEO] Detectado via IP ({ip_address}): {location}")
                return location
        else:
            print(f"[GEO] IP privado ignorado: {ip_address}")

    # 3. Ultimo recurso: Accept-Language (menos confiavel pois depende do idioma do navegador)
    if headers:
        accept_lang = headers.get("accept-language", "")
        if accept_lang:
            print(f"[GEO] Accept-Language: {accept_lang[:50]}")
            # Apenas usar se for muito claro
            if "en-US" in accept_lang and "pt" not in accept_lang.lower():
                print(f"[GEO] Detectado via Accept-Language: Estados Unidos")
                return "Estados Unidos"
            # Nao assumir Brasil so porque o idioma e portugues!

    print(f"[GEO] Nao foi possivel detectar localizacao")
    return None
