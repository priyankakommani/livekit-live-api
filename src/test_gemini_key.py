import os
import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

async def test_key():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY not found in .env")
        return

    print(f"Testing Gemini API Key: {api_key[:4]}...{api_key[-4:]}")
    
    # Target NATIVE AUDIO models
    candidates = [
        "gemini-2.5-flash-native-audio-latest",
        "gemini-2.5-flash-native-audio-preview-12-2025",
    ]
    
    versions = ["v1beta", "v1alpha"]
    
    for version in versions:
        print(f"\n--- Testing API Version: {version} ---")
        client = genai.Client(api_key=api_key, http_options={'api_version': version})
        
        for model_name in candidates:
            print(f"Testing {model_name}...")
            try:
                # Add config to avoid 1007 errors
                config = {
                    "response_modalities": ["AUDIO"],
                    "speech_config": {
                        "voice_config": {
                            "prebuilt_voice_config": {
                                "voice_name": "Puck"
                            }
                        }
                    }
                }
                
                async with client.aio.live.connect(model=model_name, config=config) as session:
                    print(f"✅ SUCCESS! {model_name} CONNECTED via {version}.")
                    print(f"🚀 THIS MODEL WORKS WITH YOUR KEY!")
                    return
            except Exception as e:
                msg = str(e)
                print(f"❌ {model_name} ({version}) FAILED: {msg[:150]}")

if __name__ == "__main__":
    asyncio.run(test_key())
