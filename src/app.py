import streamlit as st
import logging
from utils import extract_video_id
from database import init_db, add_video, get_video, save_quiz, get_quiz
from curator import get_transcript, analyze_video

# --- SETUP ---
st.set_page_config(page_title="The Sanctuary", page_icon="🏛️", layout="wide")
logging.basicConfig(level=logging.INFO)
init_db()

# --- CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    .success-box { padding: 10px; background-color: #1B2618; border-left: 5px solid #4CAF50; margin-top: 10px; }
    .error-box { padding: 10px; background-color: #261818; border-left: 5px solid #FF5252; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- STATE ---
if 'current_video_id' not in st.session_state:
    st.session_state['current_video_id'] = None

# --- UI ---
def render_header():
    st.title("🏛️ The Sanctuary")
    st.caption("Verification Layer v1.0 | Signal Over Noise")
    st.divider()

def render_quiz(video_id):
    quiz_data = get_quiz(video_id)
    if not quiz_data:
        st.warning("No quiz available. (Analysis might have failed)")
        return

    st.subheader("🛡️ Verification Gate")
    score = 0
    with st.form("quiz_form"):
        for i, q in enumerate(quiz_data):
            st.markdown(f"**Q{i+1}: {q['q']}**")
            answer = st.radio(f"Select answer:", q['options'], key=f"q{i}", label_visibility="collapsed")
            st.markdown("---")
            if answer and answer.startswith(q['correct']):
                score += 1
        
        if st.form_submit_button("Submit Answers"):
            if score == len(quiz_data):
                st.balloons()
                st.markdown('<div class="success-box">✅ Access Granted.</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="error-box">❌ Failed. Score: {score}/{len(quiz_data)}</div>', unsafe_allow_html=True)

def main():
    render_header()

    with st.sidebar:
        st.header("Submit Content")
        url_input = st.text_input("YouTube URL")
        if st.button("Load Video"):
            vid = extract_video_id(url_input)
            if vid:
                st.session_state['current_video_id'] = vid
                # Trigger Analysis logic immediately?
                # Or just let the main loop handle it?
            else:
                st.error("Invalid URL")

    # MAIN DISPLAY LOGIC
    if st.session_state['current_video_id']:
        vid = st.session_state['current_video_id']
        
        # 1. ALWAYS SHOW VIDEO (The fix)
        col_video, col_quiz = st.columns([2, 1], gap="medium")
        
        with col_video:
            st.video(f"https://www.youtube.com/watch?v={vid}")
            
        # 2. Handle Analysis
        existing_video = get_video(vid)
        
        if existing_video:
            with col_quiz:
                render_quiz(vid)
        else:
            # Cold Start Analysis
            with col_quiz:
                with st.status("🔍 Analyzing...", expanded=True) as status:
                    st.write("Connecting to Piped Network...")
                    transcript = get_transcript(vid)
                    
                    if not transcript:
                        status.update(label="❌ Transcript Failed (Try another video)", state="error")
                    else:
                        st.write("Running AI Logic...")
                        analysis = analyze_video(transcript)
                        
                        if analysis:
                            add_video(vid, "Title", "Channel", transcript)
                            save_quiz(vid, analysis['questions'])
                            status.update(label="✅ Verified", state="complete")
                            st.rerun() # Refresh to show quiz
                        else:
                            status.update(label="❌ AI Error", state="error")

if __name__ == "__main__":
    main()
