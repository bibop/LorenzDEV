import asyncio
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ai.providers.openrouter import OpenRouterProvider

# Load environment variables
load_dotenv()

async def test_kimi():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key or "placeholder" in api_key:
        print("❌ Error: OPENROUTER_API_KEY not set or is a placeholder.")
        print("Please add your key to .env file.")
        return

    print(f"✅ API Key found: {api_key[:8]}...")
    print("🚀 Initializing OpenRouterProvider with Kimi k2.5...")
    
    provider = OpenRouterProvider(api_key=api_key)
    
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant. Answer briefly."},
        {"role": "user", "content": "Who are you and what version are you?"}
    ]
    
    try:
        print("\nSending request to OpenRouter (moonshotai/kimi-k2.5)...")
        response, input_tokens, output_tokens = await provider.complete(
            messages=messages,
            model="moonshotai/kimi-k2.5"
        )
        
        print("\n✅ Success! Response received:")
        print("-" * 50)
        print(response)
        print("-" * 50)
        print(f"📊 Stats: Input Tokens: {input_tokens}, Output Tokens: {output_tokens}")
        
    except Exception as e:
        print(f"\n❌ Request failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_kimi())
