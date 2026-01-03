import streamlit as st
import logging
from utils import extract_video_id
from database import init_db, add_video, get_video, save_quiz, get_quiz
from curator import analyze_text_direct

# --- SETUP ---
st.set_page_config(page_title="The Sanctuary", page_icon="🏛️", layout="wide")
logging.basicConfig(level=logging.INFO)
init_db()

# --- CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    .success-box { padding: 10px; background-color: #1B2618; border-left: 5px solid #4CAF50; margin-top: 10px; }
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
                st.error(f"❌ Verification Failed. Score: {score}/{len(quiz_data)}")

def main():
    st.title("🏛️ The Sanctuary")
    st.caption("Sovereign Verification Layer | Manual Override Active")
    st.divider()

    # --- SIDEBAR: DUAL INPUT ---
    with st.sidebar:
        st.header("Ingestion Protocol")
        url_input = st.text_input("1. YouTube URL")
        
        # The "Sovereign" Input
        transcript_input = st.text_area("2. Paste Transcript Here", height=300, 
            help="Copy the transcript from YouTube (Show Transcript -> Toggle Timestamps -> Copy).")
        
        if st.button("Mint to Library"):
            vid = extract_video_id(url_input)
            if vid and transcript_input:
                st.session_state['current_video_id'] = vid
                
                # Direct AI Analysis on the pasted text
                with st.spinner("Processing Logic..."):
                    analysis = analyze_text_direct(transcript_input)
                    if analysis:
                        add_video(vid, "Manual Entry", "Unknown", transcript_input)
                        save_quiz(vid, analysis['questions'])
                        st.success("✅ Minted successfully!")
                        st.rerun()
                    else:
                        st.error("AI Analysis Failed. Check text quality.")
            else:
                st.warning("Please provide both URL and Transcript.")

    # --- MAIN STAGE ---
    if st.session_state['current_video_id']:
        vid = st.session_state['current_video_id']
        col_video, col_quiz = st.columns([2, 1], gap="medium")
        
        with col_video:
            st.video(f"https://www.youtube.com/watch?v={vid}")
        
        with col_quiz:
            # Check if quiz exists
            if get_quiz(vid):
                render_quiz(vid)
            else:
                st.info("👈 Paste transcript in sidebar to generate Quiz.")

if __name__ == "__main__":
    main()
