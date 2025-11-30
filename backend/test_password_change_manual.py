"""
Manual test to set password_must_be_changed flag and test the flow.
"""
import asyncio
from sqlalchemy import select, update
from app.core.database import AsyncSessionLocal
from app.models.user import User


async def set_password_flag():
    """Set password_must_be_changed=True for test client."""
    async with AsyncSessionLocal() as db:
        # Update the test client
        await db.execute(
            update(User)
            .where(User.email == "client@testgym.com")
            .values(password_must_be_changed=True)
        )
        await db.commit()

        # Verify
        result = await db.execute(
            select(User).where(User.email == "client@testgym.com")
        )
        user = result.scalar_one()

        print(f"✓ Set password_must_be_changed=True for {user.email}")
        print(f"  Current value: {user.password_must_be_changed}")


if __name__ == "__main__":
    asyncio.run(set_password_flag())
