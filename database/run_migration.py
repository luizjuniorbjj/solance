"""
Script para rodar migrations no Railway PostgreSQL

Uso:
  set DATABASE_URL=postgresql://...@...railway.app:5432/railway
  python database/run_migration.py migrations/add_language_column.sql
"""
import asyncio
import asyncpg
import sys
import os

RAILWAY_DATABASE_URL = os.getenv("DATABASE_URL")

if not RAILWAY_DATABASE_URL:
    print("ERRO: DATABASE_URL nao configurada!")
    print("Configure a variavel de ambiente antes de executar:")
    print("  set DATABASE_URL=postgresql://user:pass@host:port/db")
    sys.exit(1)

async def run_migration(migration_file: str):
    print(f"Conectando ao PostgreSQL...")

    try:
        conn = await asyncpg.connect(RAILWAY_DATABASE_URL)
        print("Conectado!")

        # Ler o arquivo de migration
        print(f"Lendo {migration_file}...")
        with open(migration_file, "r", encoding="utf-8") as f:
            migration_sql = f.read()

        # Executar a migration
        print("Executando migration...")
        await conn.execute(migration_sql)

        print("Migration executada com sucesso!")

        # Verificar colunas da tabela user_profiles
        columns = await conn.fetch("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns
            WHERE table_name = 'user_profiles'
            AND column_name IN ('language', 'spoken_language', 'voice')
            ORDER BY column_name
        """)

        print(f"\nColunas adicionadas ({len(columns)}):")
        for col in columns:
            print(f"   - {col['column_name']}: {col['data_type']} (default: {col['column_default']})")

        await conn.close()
        print("\nMigration concluida!")

    except Exception as e:
        print(f"ERRO: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        migration_file = "migrations/add_language_column.sql"
    else:
        migration_file = sys.argv[1]

    asyncio.run(run_migration(migration_file))
