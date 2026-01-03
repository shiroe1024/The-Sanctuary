"""
MODULE: app.py
PURPOSE: The User Interface (Streamlit) for The Sanctuary.
STANDARDS: NASA JPL Python Adaptation
AUTHOR: The Sanctuary Architect
DATE: 2026-01-03
"""

import streamlit as st
import json
import logging
from utils import extract_video_id
from database import init_db, add_video, get_video, save_quiz, get_quiz
from curator import get_transcript, analyze_video

# --- 1. SETUP ---
st.set_page_config(page_title="The Sanctuary", page_icon="🏛️", layout="wide")
logging.basicConfig(level=logging.INFO)

# Initialize Database on Startup
init_db()

# --- 2. CSS STYLING (The "Dark Mode" Aesthetic) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    .stButton>button { width: 100%; border-radius: 5px; }
    .success-box { padding: 10px; background-color: #1B2618; border-left: 5px solid #4CAF50; margin-top: 10px; }
    .error-box { padding: 10px; background-color: #261818; border-left: 5px solid #FF5252; margin-top: 10px; }
    /* Tighten the sidebar padding */
    .css-1d391kg { padding-top: 1rem; }
    </style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE MANAGEMENT ---
if 'current_video_id' not in st.session_state:
    st.session_state['current_video_id'] = None
if 'quiz_active' not in st.session_state:
    st.session_state['quiz_active'] = False

# --- 4. UI FUNCTIONS ---

def render_header():
    st.title("🏛️ The Sanctuary")
    st.caption("Verification Layer v1.0 | Signal Over Noise")
    st.divider()

def handle_submission(url_input):
    """
    Processes the user's video submission.
    1. Extracts ID.
    2. Checks DB (Cache).
    3. If missing, triggers Curator (AI).
    """
    video_id = extract_video_id(url_input)
    
    if not video_id:
        st.error("Invalid YouTube URL. Please check the link.")
        return

    # LOGIC FIX: Do not set session state here. Wait for verification.
    
    # Check Cache First (Efficiency)
    existing_video = get_video(video_id)
    
    if existing_video:
        st.session_state['current_video_id'] = video_id
        st.success("Video found in Library. Loading Quiz...")
    else:
        # Cold Start: Trigger AI Analysis
        with st.status("🔍 Analyzing Signal Integrity...", expanded=True) as status:
            st.write("Fetching Transcript...")
            transcript = get_transcript(video_id)
            
            if not transcript:
                status.update(label="Analysis Failed: No English Transcript found.", state="error")
                return

            st.write("Running Logic Analysis (GPT-4o)...")
            analysis = analyze_video(transcript)
            
            if not analysis:
                status.update(label="Analysis Failed: AI Error.", state="error")
                return
            
            # Save to Database
            add_video(video_id, "Unknown Title", "Unknown Channel", transcript) 
            save_quiz(video_id, analysis['questions'])
            
            # NOW we set the session state, only after success
            st.session_state['current_video_id'] = video_id
            status.update(label="✅ Verified & Archived", state="complete")

def render_quiz(video_id):
    """
    Displays the Quiz Overlay.
    """
    quiz_data = get_quiz(video_id)
    
    if not quiz_data:
        st.warning("Quiz data corrupted or missing.")
        return

    st.subheader("🛡️ Verification Gate")
    st.caption("Prove comprehension to unlock the discussion.")

    # Loop through questions
    score = 0
    with st.form("quiz_form"):
        for i, q in enumerate(quiz_data):
            st.markdown(f"**Q{i+1}: {q['q']}**")
            answer = st.radio(f"Select answer:", q['options'], key=f"q{i}", label_visibility="collapsed")
            
            st.markdown("---") # Visual separator between questions

            # Simple check: Does the selected string start with the correct letter?
            if answer and answer.startswith(q['correct']):
                score += 1
        
        submitted = st.form_submit_button("Submit Answers")
        
        if submitted:
            if score == len(quiz_data):
                st.balloons()
                st.markdown('<div class="success-box">✅ Access Granted. You may now comment.</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="error-box">❌ Verification Failed. Score: {score}/{len(quiz_data)}. Rewatch the video.</div>', unsafe_allow_html=True)

# --- 5. MAIN EXECUTION FLOW ---

def main():
    render_header()

    # Sidebar: Input
    with st.sidebar:
        st.header("Submit Content")
        url_input = st.text_input("YouTube URL")
        if st.button("Analyze"):
            handle_submission(url_input)
        
        st.info("💡 Paste a Tier 1 or Tier 2 video link to mint it to the library.")

    # Main Area
    if st.session_state['current_video_id']:
        vid = st.session_state['current_video_id']
        
        # THEATER MODE LAYOUT
        # Col 1 (Video): 65% width
        # Col 2 (Quiz): 35% width
        col_video, col_quiz = st.columns([2, 1], gap="medium")
        
        with col_video:
            st.video(f"https://www.youtube.com/watch?v={vid}")
            
        with col_quiz:
            render_quiz(vid)

    else:
        # Empty State
        st.info("👈 Paste a YouTube link in the sidebar to begin.")
        st.markdown("""
        ### Supported Sources
        * **Science:** Nature, Veritasium, PBS Space Time
        * **Tech:** MIT OpenCourseWare, Computerphile
        * **History:** Fall of Civilizations
        """)

if __name__ == "__main__":
    main()