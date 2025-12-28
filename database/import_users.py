"""
Script para importar usuários do backup local para o Railway
"""
import asyncio
import asyncpg

RAILWAY_URL = "postgresql://postgres:xHvevFIkoLZjOhnVIpgNfCBohVwZkOqi@switchback.proxy.rlwy.net:42816/railway"

# Dados dos usuários extraídos do backup
USERS = [
    {
        "id": "193c910b-629c-4bdd-8302-8baf50a73e33",
        "email": "maxwell.ciriaco1991@gmail.com",
        "password_hash": "$2b$12$MKfi0KBcyh5cofBRpeL6tu3Zw/b8W5SrbyCX9QE6HxTQwCwsR46Vy",
        "is_active": True,
        "is_premium": False,
        "trial_messages_used": 2,
        "total_messages": 2,
        "accepted_terms": True,
        "accepted_privacy": True
    },
    {
        "id": "5dcfcba8-4b12-4344-af8e-e734c68d195a",
        "email": "jhennysama@icloud.com",
        "password_hash": "$2b$12$VG136gy2V5uYXiaRAL4LmuD9UhbCAcLzFMRFqJ8w70D7cQHkEK1py",
        "is_active": True,
        "is_premium": False,
        "trial_messages_used": 8,
        "total_messages": 8,
        "accepted_terms": True,
        "accepted_privacy": True
    },
    {
        "id": "aac61923-7730-4691-895f-8d14aaf2d473",
        "email": "paolapmf12@gmail.com",
        "password_hash": "$2b$12$w9rvvWK8lrOPkRRopS521.5X7RpUvRy0qO5LZhJD2z7cMhby3RFne",
        "is_active": True,
        "is_premium": True,
        "trial_messages_used": 64,
        "total_messages": 64,
        "accepted_terms": True,
        "accepted_privacy": True
    },
    {
        "id": "94a61709-616f-4999-b4c2-69116dea8dce",
        "email": "pra.izilda@homail.com",
        "password_hash": "$2b$12$Lrnc5qSes375Dz9l/nVI3.u0J7ji653wWyAkyD.H7FqEEeTF423ry",
        "is_active": True,
        "is_premium": False,
        "trial_messages_used": 4,
        "total_messages": 4,
        "accepted_terms": True,
        "accepted_privacy": True
    },
    {
        "id": "dbb82c3b-715c-49f7-a33f-5df195a24591",
        "email": "manuelafs12@gmail.com",
        "password_hash": "$2b$12$JQGpDKq.hO1bl9YLDZskq.yo3AMx7mXR067fLpA38vOA1lRNwCW/i",
        "is_active": True,
        "is_premium": False,
        "trial_messages_used": 6,
        "total_messages": 6,
        "accepted_terms": True,
        "accepted_privacy": True
    },
    {
        "id": "1e868db6-0ae4-46dd-a068-c22f60f5d489",
        "email": "jullycat11@hotmail.com",
        "password_hash": "$2b$12$421WgnCSxr/lWfMEbIzXs.xdD/LQxUk9kSNOH7le.QRPoxtSy74My",
        "is_active": True,
        "is_premium": False,
        "trial_messages_used": 12,
        "total_messages": 12,
        "accepted_terms": True,
        "accepted_privacy": True
    },
    {
        "id": "c980af15-468d-4433-9515-c4528ef452f5",
        "email": "luizjuniorbjj@gmail.com",
        "password_hash": "$2b$12$WhCBhKiLi.uruuR8XzHR9e46VVs9ZSMiz3jhliGM.CHUWSu//oVNe",
        "is_active": True,
        "is_premium": True,
        "trial_messages_used": 0,
        "total_messages": 21,
        "subscription_status": "beta_active",
        "accepted_terms": True,
        "accepted_privacy": True
    }
]

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
