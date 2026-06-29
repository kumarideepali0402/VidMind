import streamlit as st
from main import run_pipeline
from core.rag_engine import ask_question

st.set_page_config(page_title="AI Video Assistant", page_icon="🎬", layout="wide")

st.title("🎬 AI Video Assistant")
st.caption("Transcribe, summarize, and chat with any meeting or video.")

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Input")
    source = st.text_input(
        "YouTube URL or local file path",
        placeholder="https://youtube.com/... or C:/path/to/file.mp4",
    )
    language = st.selectbox("Language", ["english", "hinglish"])
    run_btn = st.button("Analyze", type="primary", use_container_width=True)

    if st.session_state.get("result"):
        st.divider()
        if st.button("Clear / New Video", use_container_width=True):
            for key in ["result", "chat_history"]:
                st.session_state.pop(key, None)
            st.rerun()

# ── Run pipeline ─────────────────────────────────────────────────────────────
if run_btn:
    if not source.strip():
        st.sidebar.error("Please enter a URL or file path.")
    else:
        st.session_state.pop("result", None)
        st.session_state.pop("chat_history", None)

        with st.status("Processing video…", expanded=True) as status:
            st.write("Downloading / loading audio…")
            try:
                result = run_pipeline(source.strip(), language)
                st.write("Transcription complete.")
                st.write("Generating summary and insights…")
                st.session_state["result"] = result
                st.session_state["chat_history"] = []
                status.update(label="Done!", state="complete", expanded=False)
            except Exception as e:
                status.update(label="Failed", state="error", expanded=True)
                st.error(f"Error: {e}")

# ── Results ───────────────────────────────────────────────────────────────────
result = st.session_state.get("result")

if result:
    st.header(f"📌 {result['title']}")
    st.divider()

    tab_summary, tab_actions, tab_decisions, tab_questions, tab_transcript, tab_chat = st.tabs(
        ["Summary", "Action Items", "Key Decisions", "Open Questions", "Transcript", "Chat"]
    )

    with tab_summary:
        st.subheader("Meeting Summary")
        st.markdown(result["summary"])

    with tab_actions:
        st.subheader("Action Items")
        st.markdown(result["action_items"])

    with tab_decisions:
        st.subheader("Key Decisions")
        st.markdown(result["key_decisions"])

    with tab_questions:
        st.subheader("Open Questions")
        st.markdown(result["open_questions"])

    with tab_transcript:
        st.subheader("Full Transcript")
        with st.expander("Show transcript", expanded=False):
            st.text_area("", value=result["transcript"], height=400, label_visibility="collapsed")

    with tab_chat:
        st.subheader("Chat with your video")

        chat_history = st.session_state.get("chat_history", [])

        # Render existing messages
        for msg in chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # New user message
        user_input = st.chat_input("Ask anything about the video…")
        if user_input:
            chat_history.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                with st.spinner("Thinking…"):
                    answer = ask_question(result["rag_chain"], user_input)
                st.markdown(answer)

            chat_history.append({"role": "assistant", "content": answer})
            st.session_state["chat_history"] = chat_history

else:
    st.info("Enter a YouTube URL or local file path in the sidebar and click **Analyze** to get started.")
