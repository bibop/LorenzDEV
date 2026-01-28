import asyncio
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ai.orchestrator import SaaSAIOrchestrator, TaskType

# Load environment variables
load_dotenv()

async def test_router():
    print("🚀 Initializing SaaSAIOrchestrator...")
    orchestrator = SaaSAIOrchestrator()
    
    # Test 1: Simple Chat (Should route to Llama 3.3 or fast model)
    print("\n[TEST 1] Simple Chat Query")
    query_chat = "Ciao, come stai?"
    result_chat = await orchestrator.process(prompt=query_chat)
    
    print(f"Query: {query_chat}")
    print(f"Selected Model: {result_chat.get('model')}")
    print(f"Task Type: {result_chat.get('task_type')}")
    print(f"Success: {result_chat.get('success')}")
    
    # Test 2: Complex Coding (Should route to Kimi k2.5)
    print("\n[TEST 2] Complex Coding Query")
    query_code = "Scrivi una funzione Python per calcolare la sequenza di Fibonacci using dynamic programming."
    result_code = await orchestrator.process(prompt=query_code)
    
    print(f"Query: {query_code}")
    print(f"Selected Model: {result_code.get('model')}")
    print(f"Task Type: {result_code.get('task_type')}")
    print(f"Success: {result_code.get('success')}")

    # Test 3: Streaming (Coding - Kimi)
    print("\n[TEST 3] Streaming Coding Query (Kimi)")
    query_stream = "Spiega brevemente la teoria della relatività."
    print(f"Query: {query_stream}")
    
    token_count = 0
    model_name = "unknown"
    
    async for chunk in orchestrator.stream(prompt=query_stream, task_type=TaskType.REASONING):
        if chunk.get("type") == "meta":
            model_name = chunk.get("model")
            print(f"Streaming Model: {model_name}")
        elif chunk.get("type") == "text":
            print(chunk.get("content"), end="", flush=True)
            token_count += 1
            
    print(f"\n\nStream complete. Estimated chunks: {token_count}")

if __name__ == "__main__":
    asyncio.run(test_router())
