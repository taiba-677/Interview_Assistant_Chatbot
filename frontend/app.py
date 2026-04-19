
import streamlit as st
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Interview Prep Chatbot",
    page_icon="💼",
    layout="wide",
)

# ================= CSS =================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stButton>button {
    background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
    color: white;
    border-radius: 8px;
    font-weight: 600;
}

.stButton>button:hover {
    transform: translateY(-2px);
}
</style>
""", unsafe_allow_html=True)

def load_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except Exception:
        pass

load_css("frontend/style.css")

# ================= API =================
BACKEND_BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
BACKEND_UPLOAD_URL = f"{BACKEND_BASE_URL}/upload"
BACKEND_CHAT_URL = f"{BACKEND_BASE_URL}/prep-chat"
BACKEND_GENERATE_URL = f"{BACKEND_BASE_URL}/generate-questions"
BACKEND_EVALUATE_URL = f"{BACKEND_BASE_URL}/evaluate-session"

# ================= SESSION STATE =================
if "mock_resume_id" not in st.session_state:
    st.session_state.mock_resume_id = None
if "interview_resume_id" not in st.session_state:
    st.session_state.interview_resume_id = None
if "active_session_id" not in st.session_state:
    st.session_state.active_session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "edit_idx" not in st.session_state:
    st.session_state.edit_idx = None
if "trigger_backend" not in st.session_state:
    st.session_state.trigger_backend = False
if "answer_reset_counter" not in st.session_state:
    st.session_state.answer_reset_counter = 0

# --- Interview Mode States ---
if "interview_count" not in st.session_state:
    st.session_state.interview_count = 0
if "interview_transcript" not in st.session_state:
    st.session_state.interview_transcript = []
if "evaluation_result" not in st.session_state:
    st.session_state.evaluation_result = None

# ================= SIDEBAR =================

with st.sidebar:
    st.markdown("<h3 style='margin:0;'><span style='background: linear-gradient(135deg, #6366f1, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800;'>Control Panel</span></h3>", unsafe_allow_html=True)

    # ================= NAVIGATION =================
    app_mode = st.radio(
        "Navigation",
        ["💬 Mock Interview", "🎯 Interview Question"]
    )

    # ---------- "New Session" button with mode-specific clearing ----------
    if st.button("➕ New Session", use_container_width=True):
        if app_mode == "💬 Mock Interview":
            # Mock Interview: Clear chat and session
            st.session_state.mock_resume_id = None
            st.session_state.active_session_id = None
            st.session_state.messages = []
            st.session_state.pop("sessions_💬 Mock Interview", None)
        else:
            # Interview Question: Clear interview states
            st.session_state.interview_resume_id = None
            st.session_state.interview_count = 0
            st.session_state.interview_transcript = []
            st.session_state.evaluation_result = None
            if "current_generated_q" in st.session_state:
                del st.session_state.current_generated_q
            st.session_state.pop("sessions_🎯 Interview Question", None)
        st.rerun()

    # ================= Conditional session fetching =================
    if app_mode == "💬 Mock Interview":
        sessions_endpoint = f"{BACKEND_BASE_URL}/mock-sessions"
    else:
        sessions_endpoint = f"{BACKEND_BASE_URL}/sessions"

    cache_key = f"sessions_{app_mode}"

    if cache_key not in st.session_state or st.session_state[cache_key] is None:
        try:
            res = requests.get(sessions_endpoint)
            if res.status_code == 200:
                st.session_state[cache_key] = res.json().get("sessions", [])
            else:
                st.session_state[cache_key] = []
        except Exception as e:
            st.session_state[cache_key] = []

    session_list = st.session_state.get(cache_key, [])

    if app_mode == "🎯 Interview Question":
        session_list = [s for s in session_list if not s.get("is_active")]

    # Ensure newest sessions appear first
    if session_list:
        try:
            session_list.sort(key=lambda s: s.get("created_at", ""), reverse=True)
        except Exception:
            pass

    # ================= Session list display =================
    st.markdown("<h3 style='margin:0;'>💬 <span style='background: linear-gradient(135deg, #f59e0b, #ef4444); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800;'>Past Sessions</span></h3>", unsafe_allow_html=True)

    if session_list:
        for s in session_list:
            session_id = s['session_id']
            current_title = s['title']

            # Toggle edit mode for this session
            editing_key = f"editing_{session_id}"
            if editing_key not in st.session_state:
                st.session_state[editing_key] = False

            # Three columns: Title | Edit | Delete
            col1, col2, col3 = st.columns([0.70, 0.15, 0.15])

            with col1:
                if st.session_state[editing_key]:
                    # Show input field to rename
                    new_title = st.text_input(
                        "New title",
                        value=current_title,
                        key=f"rename_input_{session_id}",
                        label_visibility="collapsed"
                    )
                    save_col, cancel_col = st.columns(2)
                    with save_col:
                        if st.button("💾", key=f"save_rename_{session_id}", help="Save"):
                            if new_title and new_title.strip() != current_title:
                                try:
                                    # 🔁 DYNAMIC RENAME URL
                                    rename_url = f"{BACKEND_BASE_URL}/mock-sessions/{session_id}/rename" if app_mode == "💬 Mock Interview" else f"{BACKEND_BASE_URL}/sessions/{session_id}/rename"
                                    patch_res = requests.patch(
                                        rename_url,
                                        json={"new_title": new_title.strip()}
                                    )
                                    if patch_res.status_code == 200:
                                        st.session_state.pop(f"sessions_{app_mode}", None)
                                        st.session_state[editing_key] = False
                                        st.toast("✅ Session renamed!", icon="✏️")
                                        st.rerun()
                                    else:
                                        st.error("Failed to rename session")
                                except Exception as e:
                                    st.error(str(e))
                            else:
                                st.session_state[editing_key] = False
                                st.rerun()
                    with cancel_col:
                        if st.button("❌", key=f"cancel_rename_{session_id}", help="Cancel"):
                            st.session_state[editing_key] = False
                            st.rerun()
                else:
                    # Normal button to load session
                    if st.button(
                        current_title,
                        key=f"session_{session_id}",
                        use_container_width=True
                    ):
                        st.session_state.active_session_id = session_id

                        if app_mode == "💬 Mock Interview":
                            st.session_state.mock_resume_id = s["user_id"]
                            try:
                                msg_res = requests.get(
                                    f"{BACKEND_BASE_URL}/mock-sessions/{session_id}/messages"
                                )
                                if msg_res.status_code == 200:
                                    st.session_state.messages = msg_res.json().get("messages", [])
                                else:
                                    st.session_state.messages = []
                            except Exception:
                                st.session_state.messages = []
                        else:
                            st.session_state.interview_resume_id = s["user_id"]
                            st.session_state.messages = []
                            try:
                                det_res = requests.get(f"{BACKEND_BASE_URL}/sessions/{session_id}/details")
                                if det_res.status_code == 200:
                                    det_data = det_res.json()
                                    if not det_data.get("is_active"):
                                        st.session_state.interview_transcript = det_data.get("chat_history", [])
                                        st.session_state.evaluation_result = det_data.get("evaluation")
                                        if "current_generated_q" in st.session_state:
                                            del st.session_state.current_generated_q
                                        st.session_state.interview_count = len(st.session_state.interview_transcript) // 2
                                    else:
                                        pass
                            except Exception:
                                pass

                        st.rerun()

            with col2:
                # Edit button (only shown when not already editing)
                if not st.session_state[editing_key]:
                    if st.button("✏️", key=f"edit_{session_id}", help="Rename session"):
                        st.session_state[editing_key] = True
                        st.rerun()

            with col3:
                if st.button("🗑️", key=f"delete_{session_id}", help="Delete session"):
                    try:
                        # 🔁 DYNAMIC DELETE URL
                        delete_url = f"{BACKEND_BASE_URL}/mock-sessions/{session_id}" if app_mode == "💬 Mock Interview" else f"{BACKEND_BASE_URL}/sessions/{session_id}"
                        del_res = requests.delete(delete_url)
                        if del_res.ok:
                            # Clear cache
                            st.session_state.pop(f"sessions_{app_mode}", None)
                            st.session_state.pop(cache_key, None)

                            # If the deleted session is currently active, clear the appropriate states
                            if str(st.session_state.get("active_session_id")) == str(session_id):
                                st.session_state.active_session_id = None
                                st.session_state.messages = []
                                
                                if app_mode == "💬 Mock Interview":
                                    st.session_state.mock_resume_id = None
                                else:
                                    st.session_state.interview_resume_id = None

                                # Clear Interview Question Mode states
                                if app_mode == "🎯 Interview Question":
                                    if "current_generated_q" in st.session_state:
                                        del st.session_state.current_generated_q
                                    st.session_state.interview_count = 0
                                    st.session_state.interview_transcript = []
                                    st.session_state.evaluation_result = None

                            st.toast("✅ Session deleted successfully!", icon="🗑️")
                            st.rerun()
                        else:
                            st.error(f"Failed to delete session: {del_res.status_code} {del_res.text}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    else:
        st.info("No past sessions yet.")


# =========================================================
# MOCK INTERVIEW
# =========================================================
if app_mode == "💬 Mock Interview":

    if st.session_state.mock_resume_id:
        st.markdown("<h3 style='margin:0;'><span style='background: linear-gradient(135deg, #6366f1, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800;'>💬 Chat Session</span></h3>", unsafe_allow_html=True)

    # ---------- CHAT DISPLAY ----------
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            if st.session_state.get("edit_idx") == i:
                edit_content = st.text_area("Edit Message", value=msg["content"], key=f"edit_area_{i}", label_visibility="collapsed")
                c1, c2 = st.columns(2)
                if c1.button("Save & Send", key=f"save_{i}", use_container_width=True):
                    st.session_state.old_message = msg["content"]
                    st.session_state.messages[i]["content"] = edit_content
                    
                    # Truncate all messages after this one
                    st.session_state.messages = st.session_state.messages[:i+1]
                    
                    st.session_state.edit_idx = None
                    st.session_state.trigger_backend = True
                    st.rerun()
                if c2.button("Cancel", key=f"cancel_{i}", use_container_width=True):
                    st.session_state.edit_idx = None
                    st.rerun()
            else:
                st.markdown(msg["content"])
                if msg.get("references"):
                    st.markdown("**References:**")
                    for ref in msg["references"]:
                        st.markdown(f"- [{ref['title']}]({ref['url']})")
                
                # Action Icons
                ico_col1, ico_col2, _ = st.columns([0.05, 0.05, 0.9])
                if msg["role"] == "user":
                    if ico_col1.button("✏️", key=f"edit_ico_{i}", help="Edit"):
                        st.session_state.edit_idx = i
                        st.rerun()
                    if ico_col2.button("📋", key=f"copy_ico_{i}", help="Copy"):
                        content_json = json.dumps(msg['content'])
                        st.components.v1.html(f"""
                            <script>
                            function copy() {{
                                const text = {content_json};
                                if (navigator.clipboard) {{
                                    navigator.clipboard.writeText(text).catch(err => {{
                                        const el = document.createElement('textarea');
                                        el.value = text;
                                        document.body.appendChild(el);
                                        el.select();
                                        document.execCommand('copy');
                                        document.body.removeChild(el);
                                    }});
                                }} else {{
                                    const el = document.createElement('textarea');
                                    el.value = text;
                                    document.body.appendChild(el);
                                    el.select();
                                    document.execCommand('copy');
                                    document.body.removeChild(el);
                                }}
                            }}
                            copy();
                            </script>
                        """, height=0)
                        st.toast("Copied to clipboard!")
                else:
                    if ico_col1.button("📋", key=f"copy_ico_{i}", help="Copy"):
                        content_json = json.dumps(msg['content'])
                        st.components.v1.html(f"""
                            <script>
                            function copy() {{
                                const text = {content_json};
                                if (navigator.clipboard) {{
                                    navigator.clipboard.writeText(text).catch(err => {{
                                        const el = document.createElement('textarea');
                                        el.value = text;
                                        document.body.appendChild(el);
                                        el.select();
                                        document.execCommand('copy');
                                        document.body.removeChild(el);
                                    }});
                                }} else {{
                                    const el = document.createElement('textarea');
                                    el.value = text;
                                    document.body.appendChild(el);
                                    el.select();
                                    document.execCommand('copy');
                                    document.body.removeChild(el);
                                }}
                            }}
                            copy();
                            </script>
                        """, height=0)
                        st.toast("Copied to clipboard!")

    # ---------- BACKEND TRIGGER ----------
    if st.session_state.trigger_backend:
        st.session_state.trigger_backend = False

        messages = st.session_state.messages
        user_msg_idx = -1
        for idx, m in enumerate(messages):
            if m["role"] == "user":
                user_msg_idx = idx
        
        if user_msg_idx != -1:
            latest_user_message = messages[user_msg_idx]["content"]
            chat_history = messages[:user_msg_idx]

            payload = {
                "user_id": st.session_state.mock_resume_id,
                "message": latest_user_message,
                "chat_history": chat_history,
                "old_message": st.session_state.get("old_message")
            }
            
            st.session_state.old_message = None

            with st.spinner("Interviewer is typing..."):
                try:
                    res = requests.post(BACKEND_CHAT_URL, json=payload)

                    if res.status_code == 200:
                        response_data = res.json()["response"]
                        answer = response_data.get("answer", "No response.")
                        references = response_data.get("references") or []

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer,
                            "references": references[:4]
                        })

                        # Invalidate mock session cache
                        st.session_state.pop("sessions_💬 Mock Interview", None)
                        st.rerun()

                    else:
                        st.error(res.text)

                except Exception as e:
                    st.error(str(e))

    # ---------- INPUT ----------
    user_text = st.chat_input("Ask anything...")

    if user_text:
        if not st.session_state.mock_resume_id:
            st.warning("Upload resume first")
        else:
            st.session_state.messages.append({
                "role": "user",
                "content": user_text
            })
            st.session_state.trigger_backend = True
            st.rerun()

    # ---------- FILE UPLOAD ----------
    if not st.session_state.mock_resume_id:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<h4 style='text-align: center; margin-bottom: 20px;'><span style='background: linear-gradient(135deg, #6366f1, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800;'>📂 Upload Resume (PDF)</span></h4>", unsafe_allow_html=True)
            uploaded_file = st.file_uploader(
                "Upload Resume", 
                type=["pdf"], 
                key="mock_upload_new",
                label_visibility="collapsed"
            )

            if uploaded_file:
                with st.spinner("Processing Resume..."):
                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            "application/pdf"
                        )
                    }

                    try:
                        res = requests.post(BACKEND_UPLOAD_URL, files=files)

                        if res.status_code == 200:
                            st.session_state.mock_resume_id = res.json()["user_id"]
                            st.session_state.active_session_id = None
                            st.session_state.messages = []
                            st.session_state.pop(cache_key, None)
                            st.session_state.pop("sessions_💬 Mock Interview", None)
                            st.toast("Resume uploaded successfully!", icon="✅")
                            st.rerun()

                        else:
                            st.error(res.text)

                    except Exception as e:
                        st.error(str(e))

# =========================================================
# QUESTION MODE
# =========================================================
else:

    st.markdown("<h3 style='margin:0;'><span style='background: linear-gradient(135deg, #8b5cf6, #ec4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800;'>🎯 Interview Question Mode</span></h3>", unsafe_allow_html=True)

    if not st.session_state.interview_resume_id:

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<h4 style='text-align: center; margin-bottom: 20px;'><span style='background: linear-gradient(135deg, #8b5cf6, #ec4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800;'>📤 Upload Resume to Start</span></h4>", unsafe_allow_html=True)
            uploaded_file = st.file_uploader(
                "Upload Resume", 
                type=["pdf"], 
                key="interview_upload_new",
                label_visibility="collapsed"
            )
            
            if uploaded_file:
                with st.spinner("Processing Resume..."):
                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            "application/pdf"
                        )
                    }
                    try:
                        res = requests.post(BACKEND_UPLOAD_URL, files=files)

                        if res.status_code == 200:
                            user_id = res.json()["user_id"]
                            st.session_state.interview_resume_id = user_id

                            try:
                                session_res = requests.post(
                                    f"{BACKEND_BASE_URL}/generate-questions",
                                    json={"user_id": user_id}
                                )

                                if session_res.status_code == 200:
                                    session_data = session_res.json()
                                    st.session_state.current_generated_q = session_data.get("questions")
                                    st.session_state.all_sessions = None
                                    st.rerun()

                            except Exception as e:
                                st.error(f"Session creation failed: {str(e)}")                            
                            
                            try:
                                gen_res = requests.post(
                                    BACKEND_GENERATE_URL,
                                    json={"user_id": st.session_state.interview_resume_id}
                                )
                                if gen_res.status_code == 200:
                                    st.session_state.current_generated_q = gen_res.json().get("questions")
                                    st.session_state.interview_transcript.append({"role": "assistant", "content": st.session_state.current_generated_q})
                                    st.toast("Resume uploaded and questions generated!", icon="✅")
                                else:
                                    st.toast("Resume uploaded successfully!", icon="✅")
                            except:
                                st.toast("Resume uploaded successfully!", icon="✅")
                                
                            st.rerun()
                        else:
                            st.error(res.text)
                    except Exception as e:
                        st.error(str(e))

    # Auto-generate if resume present but no questions
    if st.session_state.interview_resume_id and "current_generated_q" not in st.session_state and not st.session_state.evaluation_result:
        with st.spinner("Generating AI Questions..."):
            try:
                res = requests.post(
                    BACKEND_GENERATE_URL,
                    json={"user_id": st.session_state.interview_resume_id}
                )
                if res.status_code == 200:
                    st.session_state.current_generated_q = res.json().get("questions")
                    st.session_state.interview_transcript.append({"role": "assistant", "content": st.session_state.current_generated_q})
                    st.rerun()
            except Exception as e:
                st.error("Error generating questions. Please try again.")

    # ---------- EVALUATION DISPLAY ----------
    if st.session_state.evaluation_result:
        eval_data = st.session_state.evaluation_result
        st.success("🎉 Interview Complete!")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Overall Score", f"{eval_data.get('overall_score', 0)}%")
        c2.metric("Technical", f"{eval_data.get('technical_score', 0)}/10")
        c3.metric("Behavioral", f"{eval_data.get('behavioral_score', 0)}/10")
        
        def colorful_heading(text, icon, color1, color2):
            return f"<h5 style='margin-bottom: 0.5rem; font-size: 1rem;'><span style='margin-right: 0.5rem'>{icon}</span><span style='background: linear-gradient(135deg, {color1} 0%, {color2} 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;'>{text}</span></h5>"

        st.markdown(f"<h4 style='margin-bottom: 1rem; font-size: 1.3rem;'><span style='background: linear-gradient(135deg, #f59e0b, #ef4444); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 900;'>Verdict:</span> <span style='background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 900;'>{str(eval_data.get('final_verdict', 'COMPLETED')).upper()}</span></h4>", unsafe_allow_html=True)
        st.info(eval_data.get('summary', 'Session finished successfully.'))
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(colorful_heading("Key Strengths", "✅", "#10b981", "#059669"), unsafe_allow_html=True)
            if eval_data.get('strengths'):
                for s in eval_data.get('strengths'):
                    st.markdown(f"- {s}")
            else:
                st.markdown("- No specific strengths recorded.")
                
        with col2:
            st.markdown(colorful_heading("Areas for Improvement", "⚠️", "#f43f5e", "#e11d48"), unsafe_allow_html=True)
            if eval_data.get('weaknesses'):
                for w in eval_data.get('weaknesses'):
                    st.markdown(f"- {w}")
            else:
                st.markdown("- No specific weaknesses recorded.")
                
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(colorful_heading("Recommendations", "💡", "#3b82f6", "#2563eb"), unsafe_allow_html=True)
        st.write(eval_data.get('recommendations', ''))
        
        st.markdown("---")
        
        # Transcript HTML Display
        chat_html = ""
        for msg in st.session_state.get('interview_transcript', []):
            role_class = "assistant" if msg["role"] == "assistant" else "user"
            display_role = "Interviewer" if role_class == "assistant" else "You"
            icon = "🧑‍💼" if role_class == "assistant" else "👤"
            
            chat_html += f"""
<div class="chat-message {role_class}">
<div class="message-role">{icon} {display_role}</div>
<div class="message-text">{msg["content"]}</div>
</div>
"""
        
        if not chat_html:
            chat_html = "<p>No chat history available for this session.</p>"
            
        transcript_html = f"""
<div class="chat-history-container" style="background: white; border-radius: 16px; padding: 2rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); border: 1px solid #f1f5f9; margin-top: 2rem;">
<h3 class="chat-history-title" style="margin-top: 0; margin-bottom: 2rem; font-size: 1.8rem; display: flex; align-items: center; gap: 0.75rem; border-bottom: 2px solid #f1f5f9; padding-bottom: 1rem;">💬 <span style="background: linear-gradient(135deg, #6366f1, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800;">Session Transcript</span></h3>
<div class="chat-timeline" style="display: flex; flex-direction: column; gap: 1.5rem;">
{chat_html}
</div>
</div>
"""
        st.markdown(transcript_html, unsafe_allow_html=True)
        st.markdown("<br><br>", unsafe_allow_html=True)

    # ---------- SHOW QUESTION ----------
    elif "current_generated_q" in st.session_state:
        st.info(f"Question {st.session_state.interview_count + 1} of 6")
        st.markdown(f"**Interviewer:** {st.session_state.current_generated_q}")

        answer = st.text_area("Your Answer", key=f"interview_answer_{st.session_state.answer_reset_counter}")

        if st.button("Submit Answer"):
            if not answer:
                st.warning("Please type an answer first!")
            else:
                st.session_state.interview_transcript.append({"role": "user", "content": answer})
                st.session_state.interview_count += 1
                
                if st.session_state.interview_count >= 6:
                    with st.spinner("Generating Final Evaluation..."):
                        try:
                            eval_res = requests.post(
                                BACKEND_EVALUATE_URL,
                                json={
                                    "user_id": st.session_state.interview_resume_id,
                                    "chat_history": st.session_state.interview_transcript
                                }
                            )
                            if eval_res.status_code == 200:
                                st.session_state.evaluation_result = eval_res.json()["evaluation"]
                                if "current_generated_q" in st.session_state:
                                    del st.session_state.current_generated_q
                                st.rerun()
                            else:
                                st.error("Failed to generate evaluation.")
                        except Exception as e:
                            st.error(str(e))
                else:
                    with st.spinner("Submitting answer and fetching next question..."):
                        try:
                            payload = {
                                "user_id": st.session_state.interview_resume_id,
                                "answer": answer
                            }
                            res = requests.post(
                                BACKEND_GENERATE_URL,
                                json=payload
                            )
                            if res.status_code == 200:
                                st.session_state.current_generated_q = res.json().get("questions")
                                st.session_state.interview_transcript.append({"role": "assistant", "content": st.session_state.current_generated_q})
                                st.session_state.answer_reset_counter += 1 
                                st.rerun()
                            else:
                                st.error(f"Error: {res.text}")
                        except Exception as e:
                            st.error(str(e))