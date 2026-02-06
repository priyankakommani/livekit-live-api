"""
Test Script for AI Interview Agent
Generates a test token to join the interview room
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from livekit import api

# Load environment variables
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(env_path)

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

def generate_test_token(room_name: str = "test-interview-room", participant_name: str = "test-candidate"):
    """Generate a token for testing the interview"""
    
    token = (
        api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(participant_name)
        .with_name(participant_name)
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
            )
        )
        .to_jwt()
    )
    
    return token

def create_test_room(room_name: str = "test-interview-room", candidate_id: str = "test-001", job_role: str = "software_engineer"):
    """Create a test room with metadata"""
    import asyncio
    import json
    
    async def _create():
        lk_api = api.LiveKitAPI(
            LIVEKIT_URL,
            LIVEKIT_API_KEY,
            LIVEKIT_API_SECRET,
        )
        
        # Create room with metadata
        room_metadata = json.dumps({
            "candidate_id": candidate_id,
            "job_role": job_role
        })
        
        try:
            room = await lk_api.room.create_room(
                api.CreateRoomRequest(
                    name=room_name,
                    metadata=room_metadata,
                )
            )
            print(f"✓ Room created: {room.name}")
            print(f"  Room SID: {room.sid}")
            return room
        except Exception as e:
            print(f"Room might already exist: {e}")
            return None
        finally:
            await lk_api.aclose()
    
    return asyncio.run(_create())

def main():
    print("=" * 60)
    print("AI Interview Agent - Test Setup")
    print("=" * 60)
    
    import time
    from datetime import datetime
    
    timestamp = int(time.time())
    room_name = f"test-room-{timestamp}"
    # Use a unique candidate ID to test folder creation in S3
    candidate_id = f"candidate-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    participant_name = "Test Candidate"
    
    # Create test room
    print(f"\n1. Creating test room: {room_name}")
    create_test_room(room_name, candidate_id, "software_engineer")
    
    # Generate token
    print(f"\n2. Generating access token for participant: {participant_name}")
    token = generate_test_token(room_name, participant_name)
    
    print(f"\n3. Test Connection URL:")
    print(f"   {LIVEKIT_URL}")
    
    print(f"\n4. Access Token (copy this):")
    print(f"   {token}")
    
    print(f"\n5. Test URLs:")
    print(f"\n   Option A - LiveKit Meet (Web Browser Test):")
    livekit_url_clean = LIVEKIT_URL.replace('wss://', 'https://')
    print(f"   {livekit_url_clean}")
    print(f"   Then paste the token when prompted")
    
    print(f"\n   Option B - Direct URL with token:")
    print(f"   https://meet.livekit.io/custom?liveKitUrl={LIVEKIT_URL}&token={token}")
    
    print(f"\n6. Instructions:")
    print(f"   a. Make sure your agent is running: python agent.py dev")
    print(f"   b. Open one of the URLs above in your browser")
    print(f"   c. Allow microphone access when prompted")
    print(f"   d. Start speaking - the AI interviewer should respond!")
    
    print("\n" + "=" * 60)
    print("Ready to test! The agent should join the room automatically.")
    print("=" * 60)

if __name__ == "__main__":
    main()