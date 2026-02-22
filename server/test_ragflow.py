import asyncio
import json
import logging
import os
from dotenv import load_dotenv

# Set up logging for the test
logging.basicConfig(level=logging.INFO)

# Load env before importing tools
load_dotenv()

# We need to temporarily add dummy keys if none exist for test
# but if they do exist, we'll try an actual request
os.environ.setdefault("RAGFLOW_API_KEY", "")
from config import settings
from tools.knowledge import ragflow_search

async def test_ragflow():
    print("Testing ragflow_search tool...")
    print(f"RAGFLOW_API_KEY present: {bool(settings.RAGFLOW_API_KEY)}")
    print(f"RAGFLOW_BASE_URL: {settings.RAGFLOW_BASE_URL}")
    print("-" * 40)
    
    query = "如何入驻成为音乐人？"
    
    try:
        # Ainvoke triggers the LangChain tool's async run
        result = await ragflow_search.ainvoke({"query": query})
        
        # Format the result for easy reading
        print("Result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("\nSUCCESS!")
    except Exception as e:
        print(f"\nERROR ALONG THE WAY: {e}")

if __name__ == "__main__":
    asyncio.run(test_ragflow())
