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

async def provision_user():
    """Provision a user with specified credentials"""
    email = os.getenv("USER_EMAIL")
    password = os.getenv("USER_PASSWORD")
    name = os.getenv("USER_NAME", "Biboppibus User")
    
    if not email or not password:
        logger.error("USER_EMAIL and USER_PASSWORD environment variables must be set")
        sys.exit(1)

    async with async_session() as session:
        # 1. Ensure Tenant Exists
        logger.info("Checking for tenant...")
        result = await session.execute(select(Tenant).where(Tenant.slug == "bibop-tenant"))
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            logger.info("Creating new tenant...")
            tenant = Tenant(
                id=uuid4(),
                name="Bibop Tenant",
                slug="bibop-tenant",
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
        logger.info(f"Checking for user {email}...")
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        auth_service = AuthService(session)
        hashed_password = auth_service.hash_password(password)
        
        if not user:
            logger.info(f"Creating new user: {email}...")
            user = User(
                id=uuid4(),
                tenant_id=tenant.id,
                email=email,
                password_hash=hashed_password,
                name=name,
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
        print("USER PROVISIONED")
        print("="*50)
        print(f"Email:    {email}")
        print(f"Password: {password}")
        print("="*50 + "\n")

if __name__ == "__main__":
    try:
        asyncio.run(provision_user())
    except Exception as e:
        logger.error(f"Error provisioning user: {e}")
        sys.exit(1)
