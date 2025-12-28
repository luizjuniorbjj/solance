"""
Script para importar schema.sql no Railway PostgreSQL
"""
import asyncio
import asyncpg
import sys

# Cole aqui a URL de conexão do Railway (Public Network)
# Exemplo: postgresql://postgres:SENHA@switchback.proxy.rlwy.net:42816/railway
RAILWAY_DATABASE_URL = "postgresql://postgres:xHvevFIkoLZjOhnVIpgNfCBohVwZkOqi@switchback.proxy.rlwy.net:42816/railway"

async def import_schema():
    print("🔌 Conectando ao Railway PostgreSQL...")

    try:
        conn = await asyncpg.connect(RAILWAY_DATABASE_URL)
        print("✅ Conectado!")

        # Ler o arquivo schema.sql
        print("📄 Lendo schema.sql...")
        with open("schema.sql", "r", encoding="utf-8") as f:
            schema_sql = f.read()

        # Executar o schema
        print("🚀 Executando schema...")
        await conn.execute(schema_sql)

        print("✅ Schema importado com sucesso!")

        # Verificar tabelas criadas
        tables = await conn.fetch("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)

        print(f"\n📊 Tabelas criadas ({len(tables)}):")
        for t in tables:
            print(f"   - {t['tablename']}")

        await conn.close()
        print("\n🎉 Banco de dados pronto!")

    except Exception as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(import_schema())
