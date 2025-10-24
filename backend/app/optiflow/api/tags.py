"""
Tag endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.optiflow.models.tag import Tag

router = APIRouter()


@router.get("/")
async def list_tags(
    skip: int = 0,
    limit: int = 100,
    device_id: UUID = None,
    db: AsyncSession = Depends(get_db)
):
    """List all tags"""
    stmt = select(Tag)

    if device_id:
        stmt = stmt.where(Tag.device_id == device_id)

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    tags = result.scalars().all()
    return [
        {
            "id": str(t.id),
            "name": t.name,
            "data_type": t.data_type.value,
            "unit": t.unit,
            "device_id": str(t.device_id),
            "last_value": t.last_value
        }
        for t in tags
    ]


@router.post("/")
async def create_tag(db: AsyncSession = Depends(get_db)):
    """Create a new tag (placeholder)"""
    return {"message": "Tag creation endpoint - to be implemented"}


@router.get("/{tag_id}/latest")
async def get_tag_latest(tag_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get latest tag value (placeholder)"""
    return {"message": f"Get latest value for tag {tag_id} - to be implemented"}
