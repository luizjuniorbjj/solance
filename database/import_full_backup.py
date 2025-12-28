"""
Script para importar TODOS os dados do backup local para Railway
- user_profiles
- user_memories
- conversations (sem mensagens - são criptografadas)
"""
import asyncio
import asyncpg
import re

RAILWAY_URL = "postgresql://postgres:xHvevFIkoLZjOhnVIpgNfCBohVwZkOqi@switchback.proxy.rlwy.net:42816/railway"

def parse_copy_data(sql_content: str, table_name: str, columns: list) -> list:
    """Parse COPY data from SQL backup"""
    pattern = rf"COPY public\.{table_name} \([^)]+\) FROM stdin;\n(.*?)\n\\."
    match = re.search(pattern, sql_content, re.DOTALL)
    if not match:
        return []

    rows = []
    for line in match.group(1).strip().split('\n'):
        if line and line != '\\.':
            values = line.split('\t')
            row = {}
            for i, col in enumerate(columns):
                if i < len(values):
                    val = values[i]
                    if val == '\\N':
                        row[col] = None
                    elif val == 't':
                        row[col] = True
                    elif val == 'f':
                        row[col] = False
                    else:
                        row[col] = val
                else:
                    row[col] = None
            rows.append(row)
    return rows

async def import_all():
    print("Lendo backup_local.sql...")
    with open("backup_local.sql", "r", encoding="utf-8") as f:
        sql_content = f.read()

    print("Conectando ao Railway...")
    conn = await asyncpg.connect(RAILWAY_URL)

    # 1. PROFILES
    print("\n=== IMPORTANDO PROFILES ===")
    profile_columns = [
        "id", "user_id", "nome", "apelido", "idade", "genero", "estado_civil",
        "filhos", "profissao", "cidade", "denominacao", "tempo_de_fe", "batizado",
        "data_batismo", "igreja_local", "cargo_igreja", "tom_preferido", "profundidade",
        "usa_emoji", "horario_ativo", "lutas_encrypted", "notas_pastorais_encrypted",
        "created_at", "updated_at"
    ]
    profiles = parse_copy_data(sql_content, "user_profiles", profile_columns)
    print(f"  Encontrados: {len(profiles)} perfis")

    for p in profiles:
        try:
            await conn.execute("""
                INSERT INTO user_profiles (id, user_id, nome, apelido, idade, genero, estado_civil,
                    profissao, cidade, denominacao, tempo_de_fe, batizado, igreja_local, cargo_igreja,
                    tom_preferido, profundidade, usa_emoji, horario_ativo)
                VALUES ($1::uuid, $2::uuid, $3, $4, $5::int, $6, $7, $8, $9, $10, $11, $12::bool, $13, $14, $15, $16, $17::bool, $18)
                ON CONFLICT (user_id) DO UPDATE SET
                    nome = EXCLUDED.nome,
                    apelido = EXCLUDED.apelido,
                    idade = EXCLUDED.idade,
                    genero = EXCLUDED.genero,
                    estado_civil = EXCLUDED.estado_civil,
                    profissao = EXCLUDED.profissao,
                    cidade = EXCLUDED.cidade,
                    denominacao = EXCLUDED.denominacao,
                    tempo_de_fe = EXCLUDED.tempo_de_fe,
                    batizado = EXCLUDED.batizado,
                    igreja_local = EXCLUDED.igreja_local,
                    cargo_igreja = EXCLUDED.cargo_igreja,
                    tom_preferido = EXCLUDED.tom_preferido,
                    profundidade = EXCLUDED.profundidade,
                    usa_emoji = EXCLUDED.usa_emoji,
                    horario_ativo = EXCLUDED.horario_ativo
            """,
                p["id"], p["user_id"], p.get("nome"), p.get("apelido"),
                int(p["idade"]) if p.get("idade") else None,
                p.get("genero"), p.get("estado_civil"), p.get("profissao"), p.get("cidade"),
                p.get("denominacao"), p.get("tempo_de_fe"), p.get("batizado"),
                p.get("igreja_local"), p.get("cargo_igreja"), p.get("tom_preferido") or "equilibrado",
                p.get("profundidade") or "moderada", p.get("usa_emoji", True), p.get("horario_ativo")
            )
            nome = p.get("nome") or p.get("user_id")[:8]
            print(f"    + Profile: {nome}")
        except Exception as e:
            print(f"    ! Erro profile {p.get('id')}: {e}")

    # 2. MEMORIES
    print("\n=== IMPORTANDO MEMORIES ===")
    memory_columns = [
        "id", "user_id", "categoria", "fato", "detalhes", "importancia", "mencoes",
        "ultima_mencao", "origem_conversa_id", "extraido_em", "is_active", "validado",
        "created_at", "updated_at", "status", "supersedes_id", "confidence", "payload", "fato_normalizado"
    ]
    memories = parse_copy_data(sql_content, "user_memories", memory_columns)
    print(f"  Encontradas: {len(memories)} memórias")

    imported = 0
    for m in memories:
        # Só importar memórias ativas
        if m.get("status") != "active" or not m.get("is_active"):
            continue
        try:
            await conn.execute("""
                INSERT INTO user_memories (id, user_id, categoria, fato, detalhes, importancia,
                    mencoes, is_active, validado, status, confidence, fato_normalizado)
                VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6::int, $7::int, $8::bool, $9::bool, $10, $11::numeric, $12)
                ON CONFLICT (id) DO NOTHING
            """,
                m["id"], m["user_id"], m["categoria"], m["fato"], m.get("detalhes"),
                int(m.get("importancia") or 5), int(m.get("mencoes") or 1),
                m.get("is_active", True), m.get("validado", False),
                m.get("status", "active"), float(m.get("confidence") or 0.8),
                m.get("fato_normalizado")
            )
            imported += 1
        except Exception as e:
            print(f"    ! Erro memory: {e}")

    print(f"  Importadas: {imported} memórias ativas")

    # 3. CONVERSATIONS (sem mensagens - são criptografadas)
    print("\n=== IMPORTANDO CONVERSATIONS ===")
    conv_columns = [
        "id", "user_id", "started_at", "last_message_at", "message_count", "resumo",
        "temas", "humor_inicial", "humor_final", "versiculos_citados", "decisoes_tomadas", "is_archived"
    ]
    conversations = parse_copy_data(sql_content, "conversations", conv_columns)
    print(f"  Encontradas: {len(conversations)} conversas")

    for c in conversations:
        try:
            await conn.execute("""
                INSERT INTO conversations (id, user_id, message_count, resumo, temas,
                    humor_inicial, humor_final, is_archived)
                VALUES ($1::uuid, $2::uuid, $3::int, $4, $5::jsonb, $6, $7, $8::bool)
                ON CONFLICT (id) DO NOTHING
            """,
                c["id"], c["user_id"], int(c.get("message_count") or 0), c.get("resumo"),
                c.get("temas") or "[]", c.get("humor_inicial"), c.get("humor_final"),
                c.get("is_archived", False)
            )
        except Exception as e:
            print(f"    ! Erro conv: {e}")

    print(f"  Importadas: {len(conversations)} conversas")

    # Verificar totais
    print("\n=== RESUMO FINAL ===")
    users = await conn.fetchval("SELECT COUNT(*) FROM users")
    profiles = await conn.fetchval("SELECT COUNT(*) FROM user_profiles")
    memories = await conn.fetchval("SELECT COUNT(*) FROM user_memories WHERE status = 'active'")
    convs = await conn.fetchval("SELECT COUNT(*) FROM conversations")

    print(f"  Usuários: {users}")
    print(f"  Perfis: {profiles}")
    print(f"  Memórias ativas: {memories}")
    print(f"  Conversas: {convs}")

    await conn.close()
    print("\n✅ Importação completa!")

if __name__ == "__main__":
    asyncio.run(import_all())
