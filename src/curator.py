import json
import logging
from openai import OpenAI
import streamlit as st
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI
try:
    api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
    client = OpenAI(api_key=api_key)
except Exception:
    client = None

THE_ATLAS = {
    "Formal Sciences": ["Logic", "Mathematics", "Computer Science"],
    "Natural Sciences": ["Physics", "Chemistry", "Biology"],
    "Social Sciences": ["Economics", "Psychology", "Sociology"],
    "Humanities": ["Philosophy", "History", "Literature"],
    "Applied Sciences": ["Engineering", "Medicine", "Business"]
}

def analyze_text_direct(raw_text: str):
    """
    Directly analyzes text pasted by the user.
    Zero dependency on YouTube APIs.
    """
    if not client: return None
    if len(raw_text) < 50: return None # Too short
    
    # Truncate to save tokens (approx 15k chars is plenty)
    clean_text = raw_text[:15000]

    prompt = f"""
    You are the Curator.
    TASK: Classify this text into: {json.dumps(list(THE_ATLAS.keys()))}
    Create 3 verification questions (A,B,C) based on this text.
    OUTPUT JSON: {{ "root_category": "...", "questions": [{{ "q": "...", "options": ["A..","B.."], "correct": "A" }}] }}
    TEXT: {clean_text}
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
