"""
Initialize voice library CLI command
Run: python -m app.scripts.init_voice_library
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database import SessionLocal
from app.core.voice_templates import initialize_voice_library


async def main():
    """Initialize voice library"""
    db = SessionLocal()
    
    try:
        print("Initializing voice library...")
        result = await initialize_voice_library(db)
        
        print(f"✅ Voice library initialized successfully!")
        print(f"   - {result['voices']} system voices created")
        print(f"   - {result['personas']} persona templates created")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
