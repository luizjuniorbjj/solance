"""
Script para importar usuários do backup local para o Railway
"""
import asyncio
import asyncpg

import os
import json

RAILWAY_URL = os.getenv("DATABASE_URL", "")
if not RAILWAY_URL:
    raise ValueError("DATABASE_URL não configurada. Use: set DATABASE_URL=postgresql://...")

# Carregar usuários de arquivo JSON externo (não versionado)
# Criar arquivo users_backup.json com formato:
# [{"id": "...", "email": "...", "password_hash": "...", ...}]
USERS_FILE = os.path.join(os.path.dirname(__file__), "users_backup.json")
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r") as f:
        USERS = json.load(f)
else:
    print(f"AVISO: {USERS_FILE} não encontrado. Crie o arquivo com os dados dos usuários.")
    USERS = []

async def import_users():
    print("Conectando ao Railway...")
    conn = await asyncpg.connect(RAILWAY_URL)

    print(f"Importando {len(USERS)} usuários...")

    for user in USERS:
        try:
            await conn.execute("""
                INSERT INTO users (
                    id, email, password_hash, is_active, is_premium,
                    trial_messages_used, total_messages, subscription_status,
                    accepted_terms, accepted_terms_at, accepted_privacy, accepted_privacy_at,
                    terms_version
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), $10, NOW(), '1.0'
                )
                ON CONFLICT (id) DO NOTHING
            """,
                user["id"],
                user["email"],
                user["password_hash"],
                user["is_active"],
                user["is_premium"],
                user["trial_messages_used"],
                user["total_messages"],
                user.get("subscription_status"),
                user["accepted_terms"],
                user["accepted_privacy"]
            )
            print(f"  + {user['email']}")
        except Exception as e:
            print(f"  ! Erro em {user['email']}: {e}")

    # Verificar
    count = await conn.fetchval("SELECT COUNT(*) FROM users")
    print(f"\nTotal de usuários no Railway: {count}")

    await conn.close()
    print("Pronto!")

if __name__ == "__main__":
    asyncio.run(import_users())
