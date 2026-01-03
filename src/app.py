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

if 'current_video_id' not in st.session_state:
    st.session_state['current_video_id'] = None

def render_quiz(video_id):
    quiz_data = get_quiz(video_id)
    if not quiz_data: return

    st.subheader("🛡️ Verification Gate")
    with st.form("quiz_form"):
        score = 0
        for i, q in enumerate(quiz_data):
            st.markdown(f"**Q{i+1}: {q['q']}**")
            answer = st.radio("Select:", q['options'], key=f"q{i}", label_visibility="collapsed")
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
    st.title("🏛️ The Sanctuary")
    st.caption("Enterprise Verification Layer | Powered by Supadata")
    st.divider()

    with st.sidebar:
        st.header("Submit Content")
        url_input = st.text_input("YouTube URL")
        
        if st.button("Mint Video"):
            vid = extract_video_id(url_input)
            if vid:
                st.session_state['current_video_id'] = vid
                
                # Check DB first
                if get_video(vid):
                    st.success("Loaded from Library.")
                else:
                    # COLD START: Use the API Key!
                    with st.status("🚀 Initializing Enterprise Uplink...", expanded=True) as status:
                        st.write("Contacting Supadata Proxy Node...")
                        transcript = get_transcript(vid)
                        
                        if transcript:
                            st.write("✅ Transcript Secured. Running AI...")
                            analysis = analyze_video(transcript)
                            
                            if analysis:
                                add_video(vid, "Title", "Channel", transcript)
                                save_quiz(vid, analysis['questions'])
                                status.update(label="✅ Minted Successfully", state="complete")
                                st.rerun()
                            else:
                                status.update(label="❌ AI Analysis Failed", state="error")
                        else:
                            status.update(label="❌ API Connection Failed (Check Secrets)", state="error")
            else:
                st.error("Invalid URL")

    # MAIN DISPLAY
    if st.session_state['current_video_id']:
        vid = st.session_state['current_video_id']
        col_video, col_quiz = st.columns([2, 1], gap="medium")
        
        with col_video:
            st.video(f"https://www.youtube.com/watch?v={vid}")
            
        with col_quiz:
            if get_quiz(vid):
                render_quiz(vid)

if __name__ == "__main__":
    main()
