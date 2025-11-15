"""
Database seeding script for initial data.

Creates APPLICATION_SUPPORT user and sample subscription with users for testing.
Run this after migrations to populate the database with test data.
"""
import asyncio
from uuid import uuid4
from sqlalchemy import select
from app.core.database import AsyncSessionLocal, init_db
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.subscription import Subscription, SubscriptionType, SubscriptionStatus


async def seed_support_user():
    """
    Create APPLICATION_SUPPORT user for platform administration.

    Credentials:
    - Email: support@gymapp.com
    - Password: Support123!
    - Role: APPLICATION_SUPPORT (cross-subscription access)

    IMPORTANT: Change these credentials in production!
    """
    async with AsyncSessionLocal() as db:
        try:
            # Check if support user already exists
            result = await db.execute(
                select(User).where(User.email == "support@gymapp.com")
            )
            existing_support = result.scalar_one_or_none()

            if existing_support:
                print("✓ APPLICATION_SUPPORT user already exists")
                print(f"  Email: {existing_support.email}")
                return

            # Create APPLICATION_SUPPORT user (no subscription)
            support = User(
                email="support@gymapp.com",
                role=UserRole.APPLICATION_SUPPORT,
                hashed_password=get_password_hash("Support123!"),
                is_active=True,
                profile={"name": "Platform Support"}
            )

            db.add(support)
            await db.commit()
            await db.refresh(support)

            print("✓ APPLICATION_SUPPORT user created successfully!")
            print(f"  Email: {support.email}")
            print(f"  Password: Support123!")
            print(f"  Role: {support.role.value}")
            print("\n⚠️  IMPORTANT: Change the support password in production!")

        except Exception as e:
            print(f"✗ Error creating support user: {e}")
            await db.rollback()
            raise


async def seed_test_subscription():
    """
    Create a test GYM subscription with admin, coach, and client users.

    Subscription: "Test Gym"
    - Type: GYM (single location with multiple coaches)
    - Users:
      - Admin: admin@testgym.com / Admin123!
      - Coach: coach@testgym.com / Coach123!
      - Client: client@testgym.com / Client123!
    """
    async with AsyncSessionLocal() as db:
        try:
            # Check if subscription already exists
            result = await db.execute(
                select(Subscription).where(Subscription.name == "Test Gym")
            )
            existing_sub = result.scalar_one_or_none()

            if existing_sub:
                print("✓ Test subscription already exists")
                print(f"  Name: {existing_sub.name}")
                print(f"  Type: {existing_sub.subscription_type.value}")
                return

            # Create subscription
            subscription_id = uuid4()
            subscription = Subscription(
                id=subscription_id,
                name="Test Gym",
                subscription_type=SubscriptionType.GYM,
                status=SubscriptionStatus.ACTIVE,
                features={
                    "multi_location": False,
                    "api_access": False,
                    "white_label": False,
                    "custom_branding": True
                },
                limits={
                    "max_admins": 5,
                    "max_coaches": 25,
                    "max_clients": 500,
                    "storage_gb": 50
                },
                billing_info={
                    "plan": "gym_monthly",
                    "status": "active"
                }
            )

            db.add(subscription)
            await db.flush()  # Flush to get the subscription ID

            print("✓ Test subscription created successfully!")
            print(f"  Name: {subscription.name}")
            print(f"  Type: {subscription.subscription_type.value}")
            print(f"  Status: {subscription.status.value}")

            # Create admin user
            admin = User(
                email="admin@testgym.com",
                subscription_id=subscription_id,
                role=UserRole.SUBSCRIPTION_ADMIN,
                hashed_password=get_password_hash("Admin123!"),
                is_active=True,
                profile={
                    "name": "Test Admin",
                    "phone": "+1-555-0001",
                    "bio": "Gym owner and administrator"
                }
            )
            db.add(admin)

            # Create coach user
            coach = User(
                email="coach@testgym.com",
                subscription_id=subscription_id,
                role=UserRole.COACH,
                hashed_password=get_password_hash("Coach123!"),
                is_active=True,
                profile={
                    "name": "Test Coach",
                    "phone": "+1-555-0002",
                    "bio": "Certified personal trainer",
                    "certifications": ["NASM-CPT", "CrossFit L1"]
                }
            )
            db.add(coach)

            # Create client user
            client = User(
                email="client@testgym.com",
                subscription_id=subscription_id,
                role=UserRole.CLIENT,
                hashed_password=get_password_hash("Client123!"),
                is_active=True,
                profile={
                    "name": "Test Client",
                    "phone": "+1-555-0003",
                    "age": 28,
                    "goals": ["Strength", "Muscle gain"]
                }
            )
            db.add(client)

            await db.commit()

            print("\n✓ Test users created successfully!")
            print("  Admin:")
            print(f"    Email: admin@testgym.com")
            print(f"    Password: Admin123!")
            print(f"    Role: SUBSCRIPTION_ADMIN")
            print("  Coach:")
            print(f"    Email: coach@testgym.com")
            print(f"    Password: Coach123!")
            print(f"    Role: COACH")
            print("  Client:")
            print(f"    Email: client@testgym.com")
            print(f"    Password: Client123!")
            print(f"    Role: CLIENT")

        except Exception as e:
            print(f"✗ Error creating test subscription: {e}")
            await db.rollback()
            raise


async def seed_all():
    """
    Run all seeding functions.

    This is the main entry point for database seeding.
    """
    print("\n" + "="*60)
    print("Database Seeding - Gym App Multi-Tenant Platform")
    print("="*60 + "\n")

    # Ensure database tables exist
    print("Initializing database...")
    await init_db()
    print("✓ Database initialized\n")

    # Seed APPLICATION_SUPPORT user
    print("Seeding APPLICATION_SUPPORT user...")
    await seed_support_user()
    print()

    # Seed test subscription with users
    print("Seeding test subscription and users...")
    await seed_test_subscription()
    print()

    print("="*60)
    print("Seeding complete!")
    print("="*60)
    print("\nYou can now test the API with these credentials:")
    print("  • Platform Support: support@gymapp.com / Support123!")
    print("  • Gym Admin: admin@testgym.com / Admin123!")
    print("  • Gym Coach: coach@testgym.com / Coach123!")
    print("  • Gym Client: client@testgym.com / Client123!")
    print("\nStart the server with: uv run uvicorn app.main:app --reload")
    print("Then visit: http://localhost:8000/docs")
    print("="*60 + "\n")


def main():
    """
    Entry point for running the seed script.

    Usage:
        cd backend
        uv run python -m app.core.seed
    """
    asyncio.run(seed_all())


if __name__ == "__main__":
    main()
