import streamlit as st
import sqlite3
import json
import datetime
from utils.resume_parser import parse_resume
from utils.scoring import score_candidate
from utils.fairness import compute_air, compute_error_rates
from utils.logging import log_event

# -----------------------------
# Database setup
# -----------------------------
def init_db():
    conn = sqlite3.connect('data/hiring.db')
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            resume_text TEXT,
            scores TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# -----------------------------
# UI
# -----------------------------
st.set_page_config(page_title="AI Hiring Support Tool", layout="wide")
st.title("Team Delta — AI-Enabled Hiring Support Tool")

st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to:", ["Upload Resume", "Ranked Candidates", "Fairness Dashboard"])

# -----------------------------
# Upload Resume
# -----------------------------
if page == "Upload Resume":
    st.subheader("Upload Resume")

    uploaded_file = st.file_uploader("Upload PDF or TXT resume", type=["pdf", "txt"])
    candidate_name = st.text_input("Candidate Name")

    if uploaded_file and candidate_name:
        resume_text = parse_resume(uploaded_file)
        st.write("### Extracted Resume Text")
        st.write(resume_text)

        scores = score_candidate(resume_text)
        st.write("### Predictor Scores")
        st.json(scores)

        # Save to DB
        conn = sqlite3.connect('data/hiring.db')
        c = conn.cursor()
        c.execute("""
            INSERT INTO candidates (name, resume_text, scores, timestamp)
            VALUES (?, ?, ?, ?)
        """, (candidate_name, resume_text, json.dumps(scores), str(datetime.datetime.now())))
        conn.commit()
        conn.close()

        st.success("Candidate successfully saved.")
        log_event("candidate_uploaded", {"candidate": candidate_name})

# -----------------------------
# Ranked Candidates
# -----------------------------
elif page == "Ranked Candidates":
    st.subheader("Ranked Candidates")
    conn = sqlite3.connect('data/hiring.db')
    c = conn.cursor()
    c.execute("SELECT name, scores FROM candidates")
    rows = c.fetchall()
    conn.close()

    if rows:
        candidates = []
        for name, scores_json in rows:
            scores = json.loads(scores_json)
            total = scores["conscientiousness"] + scores["learning_goal_orientation"]
            candidates.append((name, total, scores))

        ranked = sorted(candidates, key=lambda x: x[1], reverse=True)

        for name, total, scores in ranked:
            st.write(f"### {name}")
            st.write(f"Overall Score: {total}")
            st.json(scores)
            st.write("---")
    else:
        st.info("No candidates uploaded yet.")

# -----------------------------
# Fairness Dashboard
# -----------------------------
elif page == "Fairness Dashboard":
    st.subheader("Fairness Dashboard")

    conn = sqlite3.connect('data/hiring.db')
    c = conn.cursor()
    c.execute("SELECT name, scores FROM candidates")
    rows = c.fetchall()
    conn.close()

    if not rows:
        st.info("No candidates available for fairness analysis.")
    else:
        st.write("### Adverse Impact Ratio (AIR)")
        air = compute_air()
        st.write(f"AIR: {air}")

        st.write("### Error Rate Parity")
        error_rates = compute_error_rates()
        st.json(error_rates)

        st.caption("Aggregated metrics only shown when n ≥ 5.")

