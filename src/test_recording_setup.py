"""
Simple test script to verify local recording setup
"""
import os
from pathlib import Path

def check_recording_setup():
    """Check if all requirements for local recording are met"""
    
    print("=" * 60)
    print("LOCAL RECORDING SETUP VERIFICATION")
    print("=" * 60)
    
    checks_passed = []
    checks_failed = []
    
    # 1. Check if recordings directory exists
    project_root = Path(__file__).parent.parent
    recordings_dir = project_root / "recordings"
    
    if recordings_dir.exists():
        checks_passed.append(f"✓ Recordings directory exists: {recordings_dir.absolute()}")
    else:
        recordings_dir.mkdir(exist_ok=True)
        checks_passed.append(f"✓ Recordings directory created: {recordings_dir.absolute()}")
    
    # 2. Check if ffmpeg is installed
    import subprocess
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            checks_passed.append(f"✓ ffmpeg is installed: {version_line}")
        else:
            checks_failed.append("✗ ffmpeg is installed but not working properly")
    except FileNotFoundError:
        checks_failed.append("✗ ffmpeg is NOT installed - Install with: sudo apt-get install ffmpeg")
    except Exception as e:
        checks_failed.append(f"✗ Error checking ffmpeg: {e}")
    
    # 3. Check if transcripts directory exists
    transcripts_dir = Path("transcripts")
    if transcripts_dir.exists():
        checks_passed.append(f"✓ Transcripts directory exists: {transcripts_dir.absolute()}")
    else:
        transcripts_dir.mkdir(exist_ok=True)
        checks_passed.append(f"✓ Transcripts directory created: {transcripts_dir.absolute()}")
    
    # 4. Check environment variables
    env_vars = ['LIVEKIT_URL', 'LIVEKIT_API_KEY', 'LIVEKIT_API_SECRET', 'GOOGLE_API_KEY']
    for var in env_vars:
        if os.getenv(var):
            checks_passed.append(f"✓ {var} is set")
        else:
            checks_failed.append(f"✗ {var} is NOT set in .env file")
    
    # Print results
    print("\nPASSED CHECKS:")
    for check in checks_passed:
        print(f"  {check}")
    
    if checks_failed:
        print("\nFAILED CHECKS:")
        for check in checks_failed:
            print(f"  {check}")
    
    print("\n" + "=" * 60)
    
    if checks_failed:
        print("❌ Some checks failed. Please fix the issues above.")
        print("=" * 60)
        return False
    else:
        print("✅ ALL CHECKS PASSED - Local recording is ready!")
        print("=" * 60)
        return True

if __name__ == "__main__":
    check_recording_setup()