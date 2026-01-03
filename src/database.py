import sqlite3
import os
import json
from datetime import datetime

# 1. Setup the Database Path
# This forces the DB to live in the 'data' folder we created
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "data", "sanctuary.db")

def get_connection():
    """Establishes a connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)

def init_db():
    """Creates the tables if they don't exist."""
    conn = get_connection()
    c = conn.cursor()
    
    # Table 1: The Library (Videos)
    c.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            video_id TEXT PRIMARY KEY,
            title TEXT,
            channel_name TEXT,
            transcript TEXT,
            date_added TIMESTAMP
        )
    ''')

    # Table 2: The Gate (Quizzes)
    c.execute('''
        CREATE TABLE IF NOT EXISTS quizzes (
            video_id TEXT PRIMARY KEY,
            quiz_data TEXT,  -- Stores the JSON of the Q&A
            created_at TIMESTAMP,
            FOREIGN KEY(video_id) REFERENCES videos(video_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized at: {DB_PATH}")

# --- HELPER FUNCTIONS ---

def add_video(video_id, title, channel, transcript):
    """Adds a new video to the library."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO videos VALUES (?, ?, ?, ?, ?)', 
                  (video_id, title, channel, transcript, datetime.now()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Video already exists
    finally:
        conn.close()

def get_video(video_id):
    """Retrieves a video by ID."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM videos WHERE video_id = ?', (video_id,))
    row = c.fetchone()
    conn.close()
    return row

def save_quiz(video_id, quiz_json):
    """Saves the AI-generated quiz."""
    conn = get_connection()
    c = conn.cursor()
    # Ensure quiz_json is a string
    if isinstance(quiz_json, dict) or isinstance(quiz_json, list):
        quiz_json = json.dumps(quiz_json)
        
    c.execute('INSERT OR REPLACE INTO quizzes VALUES (?, ?, ?)', 
              (video_id, quiz_json, datetime.now()))
    conn.commit()
    conn.close()

def get_quiz(video_id):
    """Retrieves the quiz for a video."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT quiz_data FROM quizzes WHERE video_id = ?', (video_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return None