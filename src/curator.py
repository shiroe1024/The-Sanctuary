"""
MODULE: curator.py
PURPOSE: The 'Janitor' - Cloud Compatible Version using Official API.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from youtube_transcript_api.formatters import TextFormatter
from openai import OpenAI
# We don't need dotenv on the cloud (we use Secrets), but we keep it for local safety
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# --- 1. CONFIGURATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # On Streamlit Cloud, keys are in st.secrets, locally they are in os.getenv
    import streamlit as st
    api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
    client = OpenAI(api_key=api_key)
except Exception as e:
    logger.error(f"OpenAI Client Error: {e}")
    client = None

# --- 2. THE ATLAS ---
THE_ATLAS = {
    "Formal Sciences": ["Logic", "Mathematics", "Computer Science", "Systems Theory", "Statistics"],
    "Natural Sciences": ["Physics", "Chemistry", "Biology", "Earth Science", "Astronomy"],
    "Social Sciences": ["Economics", "Psychology", "Sociology", "Political Science", "Anthropology"],
    "Humanities": ["Philosophy", "History", "Literature", "Theology", "Arts"],
    "Applied Sciences": ["Engineering", "Medicine", "Agriculture", "Architecture", "Business"],
    "Practical Arts": ["Education", "Journalism", "Law", "Media", "Military Science"]
}

# --- 3. CORE FUNCTIONS ---

def get_transcript(video_id: str) -> Optional[str]:
    try:
        # 1. Try fetching manually created English subtitles first
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # 2. Filter for English (Manual or Auto)
        # This logic works better on US Servers than Korean ones
        transcript = transcript_list.find_transcript(['en', 'en-US'])
        
        formatter = TextFormatter()
        text_data = formatter.format_transcript(transcript.fetch())
        return text_data

    except Exception as e:
        logger.warning(f"Transcript Fetch Fail for {video_id}: {e}")
        return None

def analyze_video(transcript: str) -> Optional[Dict[str, Any]]:
    if not client: return None
    
    prompt = f"""
    TASK: Classify this text into one of these Roots: {json.dumps(list(THE_ATLAS.keys()))}
    Then create 3 verification questions (Multiple Choice).
    
    OUTPUT JSON: {{ "root_category": "...", "sub_category": "...", "questions": [...] }}
    
    TEXT: {transcript[:15000]}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return None