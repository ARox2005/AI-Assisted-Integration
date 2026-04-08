import os
import asyncio
from dotenv import load_dotenv
import httpx
from langchain_openai import ChatOpenAI

load_dotenv(".env")

async def test_nim():
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        print("ERROR: NVIDIA_API_KEY not found in .env")
        return

    print("1. Testing raw authentication with /models endpoint...")
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                "https://integrate.api.nvidia.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            res.raise_for_status()
            models = res.json().get("data", [])
            print(f"✅ Auth successful! Found {len(models)} models available on NVIDIA NIM.")
    except Exception as e:
        print(f"❌ Auth or network failed: {e}")
        return

    print("\n2. Testing meta/llama-3.1-8b-instruct via LangChain...")
    try:
        llm_llama = ChatOpenAI(
            model="meta/llama-3.1-8b-instruct",
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key,
            max_tokens=64
        )
        response = await llm_llama.ainvoke("Return exactly one word: 'Alive'")
        print(f"✅ Llama responds: {response.content.strip()}")
    except Exception as e:
        print(f"❌ Llama failed: {e}")

    print("\n3. Testing google/gemma-3n-e4b-it via LangChain...")
    try:
        llm_gemma = ChatOpenAI(
            model="google/gemma-3n-e4b-it",
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key,
            max_tokens=64,
            timeout=15 # Put a tight timeout to catch 504s faster
        )
        response = await llm_gemma.ainvoke("Return exactly one word: 'Alive'")
        print(f"✅ Gemma responds: {response.content.strip()}")
    except Exception as e:
        print(f"❌ Gemma failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_nim())
