import requests
import json
import logging
from openai import OpenAI
import streamlit as st
import os

# --- CONFIG ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    openai_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
    rapid_key = st.secrets.get("RAPIDAPI_KEY", os.getenv("RAPIDAPI_KEY"))
    client = OpenAI(api_key=openai_key)
except Exception:
    client = None

# --- CONSTANTS ---
THE_ATLAS = {
    "Formal Sciences": ["Logic", "Mathematics", "Computer Science"],
    "Natural Sciences": ["Physics", "Chemistry", "Biology"],
    "Social Sciences": ["Economics", "Psychology", "Sociology"],
    "Humanities": ["Philosophy", "History", "Literature"],
    "Applied Sciences": ["Engineering", "Medicine", "Business"]
}

def get_transcript(video_id: str):
    """
    Enterprise Method: Uses Supadata via RapidAPI.
    """
    if not rapid_key:
        logger.error("RapidAPI Key missing.")
        return None

    # SUPADATA ENDPOINT
    url = "https://youtube-transcripts.p.rapidapi.com/youtube/transcript"
    
    # Supadata expects the full URL, not just the ID
    querystring = {
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "chunkSize": "500" 
    }

    headers = {
        "x-rapidapi-key": rapid_key,
        "x-rapidapi-host": "youtube-transcripts.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers, params=querystring)
        
        if response.status_code == 200:
            data = response.json()
            
            # Supadata Format: {"content": [{"text": "...", ...}, ...]}
            if 'content' in data:
                # Join all text segments
                full_text = " ".join([item['text'] for item in data['content']])
                return full_text
            
            return str(data)
            
        else:
            logger.error(f"RapidAPI Error: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        logger.error(f"API Connection Failed: {e}")
        return None

def analyze_video(transcript: str):
    if not client: return None
    
    prompt = f"""
    Classify into Roots: {json.dumps(list(THE_ATLAS.keys()))}
    Create 3 verification questions (A,B,C) based on this text.
    OUTPUT JSON: {{ "root_category": "...", "questions": [...] }}
    TEXT: {transcript[:15000]}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception:
        return None
