import sys
import os

print(f"python executable: {sys.executable}")
print(f"cwd: {os.getcwd()}")

try:
    import youtube_transcript_api
    print(f"✅ FOUND LIBRARY AT: {youtube_transcript_api.__file__}")
    print(f"VERSION: {youtube_transcript_api.__version__}")
    
    from youtube_transcript_api import YouTubeTranscriptApi
    
    # Check if the method exists
    if hasattr(YouTubeTranscriptApi, 'list_transcripts'):
        print("✅ SUCCESS: 'list_transcripts' method exists.")
    else:
        print("❌ FAILURE: Method missing. You are loading a phantom file.")
        print(f"Dir listing: {dir(YouTubeTranscriptApi)}")

except ImportError as e:
    print(f"❌ CRITICAL: Could not import library. {e}")
except Exception as e:
    print(f"❌ ERROR: {e}")