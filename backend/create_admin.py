#!/usr/bin/env python3
"""Script para criar usuário administrador no OptiFlow AI"""
import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash

async def create_admin_user():
    admin_email = "admin@optiflow.com"
    admin_password = "admin123"
    admin_name = "Administrador OptiFlow"

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == admin_email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"❌ Usuário {admin_email} já existe!")
            print(f"\n📧 Email: {admin_email}")
            print(f"🔑 Senha: {admin_password}")
            return

        admin_user = User(
            email=admin_email,
            hashed_password=get_password_hash(admin_password),
            full_name=admin_name,
            is_active=True,
            is_superuser=True,
        )

        db.add(admin_user)
        await db.commit()
        await db.refresh(admin_user)

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

if __name__ == "__main__":
    asyncio.run(create_admin_user())
