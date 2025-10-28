"""
User endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.core.security import get_password_hash

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all users"""
    stmt = select(User).offset(skip).limit(limit)
    result = await db.execute(stmt)
    users = result.scalars().all()
    return users


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")  # 🔒 Anti-abuse: Limit user creation attempts
async def create_user(
    request: Request,
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new user"""
    # Check if user exists
    stmt = select(User).where(
        (User.email == user_in.email) | (User.username == user_in.username)
    )
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )

    # Create user
    user_data = user_in.model_dump(exclude={"password"})
    user = User(**user_data)
    user.hashed_password = get_password_hash(user_in.password)

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID"""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user
