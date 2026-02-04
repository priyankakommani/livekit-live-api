"""
Test Setup Script
Verify that all components are properly configured
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import livekit
        print("✓ LiveKit imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import LiveKit: {e}")
        return False
        
    try:
        from livekit.plugins import google
        print("✓ LiveKit Google plugin imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import Google plugin: {e}")
        return False
        
    try:
        import google.generativeai
        print("✓ Google Generative AI imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import Google Generative AI: {e}")
        return False
        
    try:
        from dotenv import load_dotenv
        print("✓ python-dotenv imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import python-dotenv: {e}")
        return False
        
    return True


def test_configuration():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    try:
        from config import config
        print("✓ Configuration module loaded")
        
        # Check required fields
        if not config.GOOGLE_API_KEY:
            print("✗ GOOGLE_API_KEY not set")
            return False
        else:
            print(f"✓ GOOGLE_API_KEY set (length: {len(config.GOOGLE_API_KEY)})")
            
        if not config.LIVEKIT_URL:
            print("✗ LIVEKIT_URL not set")
            return False
        else:
            print(f"✓ LIVEKIT_URL set: {config.LIVEKIT_URL}")
            
        if not config.LIVEKIT_API_KEY:
            print("✗ LIVEKIT_API_KEY not set")
            return False
        else:
            print(f"✓ LIVEKIT_API_KEY set (length: {len(config.LIVEKIT_API_KEY)})")
            
        if not config.LIVEKIT_API_SECRET:
            print("✗ LIVEKIT_API_SECRET not set")
            return False
        else:
            print(f"✓ LIVEKIT_API_SECRET set (length: {len(config.LIVEKIT_API_SECRET)})")
            
        return True
        
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False


def test_modules():
    """Test custom modules"""
    print("\nTesting custom modules...")
    
    try:
        import prompts
        print("✓ prompts module loaded")
        
        roles = prompts.list_available_roles()
        print(f"✓ Available roles: {', '.join(roles)}")
        
    except Exception as e:
        print(f"✗ Failed to import prompts: {e}")
        return False
        
    try:
        from recording_manager import RecordingManager
        print("✓ recording_manager module loaded")
    except Exception as e:
        print(f"✗ Failed to import recording_manager: {e}")
        return False
        
    try:
        from transcription_handler import TranscriptionHandler
        print("✓ transcription_handler module loaded")
    except Exception as e:
        print(f"✗ Failed to import transcription_handler: {e}")
        return False
        
    try:
        from evaluator import InterviewEvaluator
        print("✓ evaluator module loaded")
    except Exception as e:
        print(f"✗ Failed to import evaluator: {e}")
        return False
        
    return True


def test_directories():
    """Test that required directories exist"""
    print("\nTesting directories...")
    
    required_dirs = ['recordings', 'transcripts', 'evaluations']
    
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"✓ Directory exists: {dir_name}")
        else:
            print(f"✗ Directory missing: {dir_name}")
            return False
            
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("AI Interview System - Setup Verification")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_configuration),
        ("Custom Modules", test_modules),
        ("Directories", test_directories),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Start the agent: python src/agent.py dev")
        print("2. Connect a candidate to the LiveKit room")
        print("3. The interview will start automatically")
    else:
        print("✗ Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("1. Ensure .env file exists with all required variables")
        print("2. Run: pip install -r requirements.txt")
        print("3. Check that all API keys are valid")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
