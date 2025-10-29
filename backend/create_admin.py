"""
Script para criar usuário administrador no SmartPort
Executa no container do backend
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import sys
import os

# Configuração do banco de dados
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://optiflow:optiflow_password@postgres:5432/optiflow"
)

async def create_admin_user():
    """Criar usuário administrador"""

    # Criar engine
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        try:
            # Importar dependências necessárias
            from passlib.context import CryptContext

            # Configurar contexto de senha
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

            # Hash da senha
            password = "Admin@123456"
            hashed_password = pwd_context.hash(password)

            # SQL para criar usuário
            sql = """
                INSERT INTO users (
                    id,
                    email,
                    full_name,
                    hashed_password,
                    role,
                    is_active,
                    created_at,
                    updated_at
                )
                VALUES (
                    gen_random_uuid(),
                    :email,
                    :full_name,
                    :hashed_password,
                    :role,
                    :is_active,
                    :created_at,
                    :updated_at
                )
                ON CONFLICT (email) DO UPDATE SET
                    hashed_password = EXCLUDED.hashed_password,
                    updated_at = EXCLUDED.updated_at,
                    is_active = EXCLUDED.is_active
                RETURNING id, email, full_name, role;
            """

            # Executar SQL
            result = await session.execute(
                sql,
                {
                    "email": "admin@smartport.com",
                    "full_name": "Administrator",
                    "hashed_password": hashed_password,
                    "role": "admin",
                    "is_active": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            )

            await session.commit()

            user = result.fetchone()

            print("\n" + "="*60)
            print("✅ USUÁRIO ADMINISTRADOR CRIADO COM SUCESSO!")
            print("="*60)
            print(f"\nID:        {user[0]}")
            print(f"Email:     {user[1]}")
            print(f"Nome:      {user[2]}")
            print(f"Role:      {user[3]}")
            print(f"\n{'='*60}")
            print("CREDENCIAIS DE LOGIN:")
            print("="*60)
            print(f"\n  Email:    {user[1]}")
            print(f"  Senha:    {password}")
            print(f"\nAcesse: http://localhost:3000")
            print("="*60 + "\n")

            return True

        except Exception as e:
            print(f"\n❌ ERRO ao criar usuário: {e}")
            print(f"\nDetalhes: {str(e)}")
            await session.rollback()
            return False
        finally:
            await engine.dispose()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("CRIANDO USUÁRIO ADMINISTRADOR")
    print("="*60 + "\n")

    success = asyncio.run(create_admin_user())

    sys.exit(0 if success else 1)
