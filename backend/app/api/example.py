"""
Example API endpoint demonstrating database usage.
Remove this file when implementing real endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

router = APIRouter()


@router.get("/items")
async def get_items(db: AsyncSession = Depends(get_db)):
    """
    Example endpoint showing how to use database dependency injection.

    Usage:
    1. Create your model in app/models/
    2. Create your schema in app/schemas/
    3. Use the db session to query/insert/update/delete
    """
    # Example query (once you have models):
    # result = await db.execute(select(YourModel))
    # items = result.scalars().all()

    return {
        "message": "Example endpoint",
        "note": "Replace this with your actual implementation"
    }
