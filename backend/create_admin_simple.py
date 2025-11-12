#!/usr/bin/env python3
"""Script simplificado para criar usuário administrador"""
import asyncio
import asyncpg
import os
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_admin():
    # Conectar ao PostgreSQL diretamente
    conn = await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", "optiflow"),
        password=os.getenv("POSTGRES_PASSWORD", "optiflow123"),
        database=os.getenv("POSTGRES_DB", "optiflow"),
    )

    try:
        admin_email = "admin@optiflow.com"
        admin_password = "admin123"
        admin_name = "Administrador OptiFlow"
        
        # Hash da senha
        hashed_password = pwd_context.hash(admin_password)
        
        # Verificar se já existe
        existing = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1", admin_email
        )
        
        if existing:
            print(f"❌ Usuário {admin_email} já existe!")
            print(f"\n📧 Email: {admin_email}")
            print(f"🔑 Senha: {admin_password}")
            return
        
        # Criar usuário
        await conn.execute(
            """
            INSERT INTO users (email, hashed_password, full_name, is_active, is_superuser)
            VALUES ($1, $2, $3, $4, $5)
            """,
            admin_email,
            hashed_password,
            admin_name,
            True,
            True,
        )
        
        print("=" * 60)
        print("✅ Usuário administrador criado com sucesso!")
        print("=" * 60)
        print(f"\n📧 Email: {admin_email}")
        print(f"🔑 Senha: {admin_password}")
        print(f"👤 Nome: {admin_name}")
        print(f"🔐 Admin: Sim")
        print("\n" + "=" * 60)
        print("💡 Use estas credenciais para fazer login em:")
        print("   http://localhost:3000")
        print("=" * 60)
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_admin())
