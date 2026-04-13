import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Interview Prep Chatbot",
    page_icon="💼",
    layout="wide",
)

BACKEND_BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
BACKEND_UPLOAD_URL = f"{BACKEND_BASE_URL}/upload"
BACKEND_CHAT_URL = f"{BACKEND_BASE_URL}/prep-chat"
BACKEND_GENERATE_URL = f"{BACKEND_BASE_URL}/generate-questions"


# ---------------- TITLE ----------------
st.title("💼 Premium AI Career Coach")
st.subheader("Interactive Interview Preparation System")


# ---------------- SESSION STATE ----------------
if "resume_id" not in st.session_state:
    st.session_state.resume_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

# interview states
if "question_count" not in st.session_state:
    st.session_state.question_count = 0

if "current_question" not in st.session_state:
    st.session_state.current_question = None

if "waiting_for_answer" not in st.session_state:
    st.session_state.waiting_for_answer = False

if "qa_history" not in st.session_state:
    st.session_state.qa_history = []

if "final_feedback" not in st.session_state:
    st.session_state.final_feedback = None

# 🔥 FIX: button lock state (prevents double trigger issues)
if "gen_lock" not in st.session_state:
    st.session_state.gen_lock = False


# ---------------- SIDEBAR ----------------
with st.sidebar:
    mode = st.radio(
        "Navigation",
        ["💬 Mock Interview", "🎯 Interview Question"]
    )

    if st.session_state.resume_id:
        st.success("Resume Active")
    else:
        st.warning("No Resume Uploaded")


# =========================================================
# 💬 MOCK INTERVIEW (UNCHANGED)
# =========================================================
if mode == "💬 Mock Interview":

    st.markdown("### 🗣️ Mock Interview Chat")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Ask anything...", accept_file=True)

    if prompt:

        # ---------------- FILE UPLOAD ----------------
        if getattr(prompt, "files", None):
            uploaded_file = prompt.files[0]

            if not uploaded_file.name.endswith(".pdf"):
                st.error("Only PDF allowed")
            else:
                with st.spinner("Uploading Resume..."):
                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            "application/pdf"
                        )
                    }

                    res = requests.post(BACKEND_UPLOAD_URL, files=files)

                    if res.status_code == 200:
                        st.session_state.resume_id = res.json()["user_id"]
                        st.success("Resume Uploaded Successfully")
                    else:
                        st.error("Upload failed")

        # ---------------- CHAT ----------------
        if getattr(prompt, "text", None):
            if st.session_state.resume_id:

                st.session_state.messages.append({
                    "role": "user",
                    "content": prompt.text
                })

                payload = {
                    "user_id": st.session_state.resume_id,
                    "message": prompt.text,
                    "chat_history": st.session_state.messages
                }

                res = requests.post(BACKEND_CHAT_URL, json=payload)

                if res.status_code == 200:
                    answer = res.json()["response"]["answer"]

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer
                    })

                else:
                    st.error("Backend error")

            else:
                st.warning("Please upload resume first")

        st.rerun()


# =========================================================
# 🎯 INTERVIEW QUESTION MODE (FIXED GENERATE BUTTON ONLY)
# =========================================================
else:

    st.markdown("### 🎯 5 Question Interview Mode")

    # ---------------- RESUME CHECK ----------------
    if not st.session_state.resume_id:

        st.info("Upload your resume first")

        uploaded_file = st.file_uploader("Upload Resume", type=["pdf"])

        if uploaded_file:
            with st.spinner("Processing..."):
                files = {
                    "file": (
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        "application/pdf"
                    )
                }

                res = requests.post(BACKEND_UPLOAD_URL, files=files)

                if res.status_code == 200:
                    st.session_state.resume_id = res.json()["user_id"]
                    st.success("Uploaded!")
                    st.rerun()

    # ---------------- INTERVIEW FLOW ----------------
    else:

        # ---------------- FINAL OUTPUT ----------------
        if st.session_state.final_feedback:
            st.success("🎉 Interview Completed")

            st.markdown("## 📊 Final Evaluation")
            st.info(st.session_state.final_feedback)

            if st.button("Restart Interview"):
                st.session_state.question_count = 0
                st.session_state.qa_history = []
                st.session_state.current_question = None
                st.session_state.final_feedback = None
                st.session_state.waiting_for_answer = False
                st.session_state.gen_lock = False
                st.rerun()

        # ---------------- ACTIVE INTERVIEW ----------------
        else:

            # =====================================================
            # 🔥 FIXED GENERATE QUESTION BUTTON (STABLE VERSION)
            # =====================================================
            if (
                not st.session_state.waiting_for_answer
                and st.session_state.question_count < 5
                and not st.session_state.gen_lock
            ):

                if st.button("🔥 Generate Question", key="generate_q_btn"):

                    st.session_state.gen_lock = True

                    with st.spinner("Generating question..."):

                        try:
                            res = requests.post(
                                BACKEND_GENERATE_URL,
                                json={"user_id": st.session_state.resume_id},
                                timeout=30
                            )

                            if res.status_code == 200:
                                question = res.json().get("questions", "")

                                if question:
                                    st.session_state.current_question = question
                                    st.session_state.waiting_for_answer = True

                                else:
                                    st.error("No question received")

                            else:
                                st.error(f"Backend error: {res.text}")

                        except Exception as e:
                            st.error(f"Request failed: {str(e)}")

                        st.session_state.gen_lock = False
                        st.rerun()

            # ---------------- SHOW QUESTION ----------------
            if st.session_state.waiting_for_answer:

                st.markdown(f"### Question {st.session_state.question_count + 1}")
                st.info(st.session_state.current_question)

                answer = st.text_area("Write your answer here", height=150)

                if st.button("Submit Answer"):

                    if answer.strip():

                        st.session_state.qa_history.append({
                            "question": st.session_state.current_question,
                            "answer": answer
                        })

                        st.session_state.question_count += 1
                        st.session_state.waiting_for_answer = False
                        st.session_state.current_question = None

                        st.rerun()

                    else:
                        st.warning("Please write an answer")

            # ---------------- FINAL EVALUATION ----------------
            if st.session_state.question_count == 5:

                st.info("Generating final evaluation...")

                chat_history = []

                for qa in st.session_state.qa_history:
                    chat_history.append({
                        "role": "assistant",
                        "content": qa["question"]
                    })
                    chat_history.append({
                        "role": "user",
                        "content": qa["answer"]
                    })

                payload = {
                    "user_id": st.session_state.resume_id,
                    "message": "final evaluation",
                    "chat_history": chat_history
                }

                try:
                    res = requests.post(BACKEND_CHAT_URL, json=payload)

                    if res.status_code == 200:
                        st.session_state.final_feedback = res.json()["response"]["answer"]
                        st.rerun()
                    else:
                        st.error("Evaluation failed")

                except Exception as e:
                    st.error(str(e))