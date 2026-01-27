import asyncio
import os
import sys
import logging
from uuid import uuid4

# Add app directory to path
sys.path.append(os.getcwd())

from app.database import async_session, engine
from app.models import User, Tenant
from app.services.auth import AuthService
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_admin_user():
    """Create a default admin user and tenant"""
    async with async_session() as session:
        # 1. Ensure Tenant Exists
        logger.info("Checking for existing tenant...")
        result = await session.execute(select(Tenant).where(Tenant.slug == "admin-tenant"))
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            logger.info("Creating new admin tenant...")
            tenant = Tenant(
                id=uuid4(),
                name="Admin Tenant",
                slug="admin-tenant",
                plan="business",
                is_active=True
            )
            session.add(tenant)
            await session.commit()
            await session.refresh(tenant)
            logger.info(f"Tenant created: {tenant.id}")
        else:
            logger.info(f"Using existing tenant: {tenant.id}")

        # 2. Ensure User Exists
        email = "admin@lorenz.ai"
        password = "adminpassword123"
        
        logger.info(f"Checking for user {email}...")
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        auth_service = AuthService(session)
        hashed_password = auth_service.hash_password(password)
        
        if not user:
            logger.info("Creating new admin user...")
            user = User(
                id=uuid4(),
                tenant_id=tenant.id,
                email=email,
                password_hash=hashed_password,
                name="Admin User",
                role="owner",
                is_active=True,
                email_verified=True,
                onboarding_completed=True
            )
            session.add(user)
            await session.commit()
            logger.info("User created successfully!")
        else:
            logger.info("User already exists. Updating password...")
            user.password_hash = hashed_password
            user.is_active = True
            session.add(user)
            await session.commit()
            logger.info("User updated successfully!")

        print("\n" + "="*50)
        print("CREDENTIALS GENERATED")
        print("="*50)
        print(f"URL:      https://lorenz.bibop.com")
        print(f"Email:    {email}")
        print(f"Password: {password}")
        print("="*50 + "\n")

if __name__ == "__main__":
    try:
        asyncio.run(create_admin_user())
    except Exception as e:
        logger.error(f"Error creating user: {e}")
    finally:
        # Cleanup is handled by async context managers mostly, 
        # but explicit dispose is good practice for scripts
        pass
