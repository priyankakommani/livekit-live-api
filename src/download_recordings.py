"""
Download recordings from LiveKit Cloud
"""
import os
import asyncio
import httpx
from pathlib import Path
from dotenv import load_dotenv
from livekit import api

# Load environment variables
load_dotenv()

async def list_recordings():
    """List all available recordings"""
    print("=" * 60)
    print("AVAILABLE RECORDINGS IN LIVEKIT CLOUD")
    print("=" * 60)
    
    livekit_api = api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET")
    )
    
    try:
        # List all egress (recordings)
        egress_list = await livekit_api.egress.list_egress()
        
        if not egress_list:
            print("\n⚠ No recordings found")
            return []
        
        recordings = []
        for i, egress in enumerate(egress_list, 1):
            print(f"\n{i}. Recording ID: {egress.egress_id}")
            print(f"   Room: {egress.room_name}")
            print(f"   Status: {egress.status}")
            print(f"   Started: {egress.started_at}")
            
            if egress.file_results:
                for file_result in egress.file_results:
                    print(f"   File: {file_result.filename}")
                    if file_result.download_url:
                        print(f"   Download URL: {file_result.download_url}")
                        recordings.append({
                            'egress_id': egress.egress_id,
                            'filename': file_result.filename,
                            'url': file_result.download_url,
                            'room': egress.room_name
                        })
        
        return recordings
        
    finally:
        await livekit_api.aclose()

async def download_recording(url: str, output_path: str):
    """Download a recording file"""
    print(f"\nDownloading to: {output_path}")
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        async with client.stream('GET', url) as response:
            response.raise_for_status()
            
            total = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(output_path, 'wb') as f:
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Progress indicator
                    if total > 0:
                        percent = (downloaded / total) * 100
                        print(f"\rProgress: {percent:.1f}% ({downloaded}/{total} bytes)", end='')
            
            print(f"\n✓ Downloaded successfully: {output_path}")

async def download_all_recordings():
    """Download all available recordings"""
    # Create downloads directory
    downloads_dir = Path("downloads")
    downloads_dir.mkdir(exist_ok=True)
    
    # List recordings
    recordings = await list_recordings()
    
    if not recordings:
        return
    
    print("\n" + "=" * 60)
    print("DOWNLOADING RECORDINGS")
    print("=" * 60)
    
    # Download each recording
    for recording in recordings:
        output_path = downloads_dir / recording['filename']
        
        # Skip if already downloaded
        if output_path.exists():
            print(f"\n⚠ Skipping {recording['filename']} (already exists)")
            continue
        
        try:
            await download_recording(recording['url'], str(output_path))
        except Exception as e:
            print(f"\n✗ Error downloading {recording['filename']}: {e}")
    
    print("\n" + "=" * 60)
    print("✓ ALL RECORDINGS DOWNLOADED")
    print(f"Location: {downloads_dir.absolute()}")
    print("=" * 60)

async def download_by_room(room_name: str):
    """Download recording for a specific room"""
    recordings = await list_recordings()
    
    matching = [r for r in recordings if room_name in r['room']]
    
    if not matching:
        print(f"\n⚠ No recordings found for room: {room_name}")
        return
    
    downloads_dir = Path("downloads")
    downloads_dir.mkdir(exist_ok=True)
    
    print("\n" + "=" * 60)
    print(f"DOWNLOADING RECORDING FOR ROOM: {room_name}")
    print("=" * 60)
    
    for recording in matching:
        output_path = downloads_dir / recording['filename']
        
        try:
            await download_recording(recording['url'], str(output_path))
        except Exception as e:
            print(f"\n✗ Error: {e}")

def main():
    """Main function with CLI"""
    import sys
    
    if len(sys.argv) > 1:
        # Download specific room
        room_name = sys.argv[1]
        asyncio.run(download_by_room(room_name))
    else:
        # Download all recordings
        asyncio.run(download_all_recordings())

if __name__ == "__main__":
    main()