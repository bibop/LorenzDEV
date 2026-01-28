
import asyncio
import sys
import os

# Add parent dir to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import async_session
from app.services.auth import AuthService
from app.schemas.auth import UserCreate
from app.models import User
# Fix for registry error: import UnifiedContact
from app.models.social_graph import UnifiedContact
from sqlalchemy import select

async def debug_auth():
    async with async_session() as db:
        print("--- DEBUGGING AUTH ---")
        email = "bibop@bibop.com"
        
        # 1. Check if user exists
        print(f"Checking if user {email} exists...")
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if user:
            print(f"❌ User ALREADY EXISTS! ID: {user.id}")
            print("This explains the 400 Bad Request (Email already registered).")
            
            # Optional: Delete user to clean up?
            print("Deleting user to allow fresh registration check...")
            await db.delete(user)
            await db.commit()
            print("✅ User deleted. You should be able to register now.")
            return

        print("✅ User does not exist.")

        # 2. Simulate Signup Logic
        print("Simulating Signup with 'BibopBibop1'...")
        auth_service = AuthService(db)
        user_data = UserCreate(
            email=email,
            password="BibopBibop1",
            name="Bibop User",
            workspace_name="Bibop Workspace"
        )
        
        try:
            token = await auth_service.create_user(user_data)
            print("✅ Signup simulation SUCCESS!")
            print(f"Access Token: {token.access_token[:20]}...")
            
            # Clean up test user
            print("Cleaning up test user...")
            # Re-fetch to delete
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            if user:
                await db.delete(user)
                await db.commit()
            
        except ValueError as e:
            print(f"❌ Signup simulation FAILED: {e}")
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_auth())
