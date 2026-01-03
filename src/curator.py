import logging
import json
import yt_dlp
import requests
from openai import OpenAI
import streamlit as st
import os

# --- CONFIG ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI (Cloud or Local)
try:
    api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
    client = OpenAI(api_key=api_key)
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
    The 'Reddit Method': Uses yt-dlp to grab subtitle data 
    without logging in or using the official API.
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    # Configure yt-dlp to only look for text (no video download)
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en'],
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # 1. Try Manual English Subs
            if 'subtitles' in info and 'en' in info['subtitles']:
                sub_url = info['subtitles']['en'][0]['url']
            # 2. Try Auto-Generated English Subs
            elif 'automatic_captions' in info and 'en' in info['automatic_captions']:
                sub_url = info['automatic_captions']['en'][0]['url']
            else:
                return None

            # 3. Download the text content
            response = requests.get(sub_url)
            try:
                # YouTube often returns JSON3 format
                data = response.json()
                text_content = " ".join([e['utf8'] for e in data['events'] if 'utf8' in e])
                return text_content
            except:
                # Fallback for raw text
                return response.text

    except Exception as e:
        logger.error(f"yt-dlp error: {e}")
        return None

def analyze_video(transcript: str):
    if not client: return None
    
    # Quick prompt to save tokens
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
