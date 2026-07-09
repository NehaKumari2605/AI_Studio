import streamlit as st
from st_copy import copy_button
from PIL import Image
import json
import os
import tempfile
import re
from chatbot import create_chat, stream_response
from utils import (
    add_message,
    export_chat,
    conversation_stats,
    get_last_response,
    load_history,
    save_history
)
def load_css():
    with open("style.css") as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )

load_css()

# ================= Page Config =================
st.set_page_config(
    page_title="AI Studio",
    page_icon="🤖",
    layout="centered"
)

# ================= Session State =================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "selected_model" not in st.session_state:
    st.session_state.selected_model = "Gemini 2.5 Flash"

if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = load_history()

if "page" not in st.session_state:
    st.session_state.page = "chat"

if "current_chat_index" not in st.session_state:
    st.session_state.current_chat_index = None

# Generation Settings
if "temperature" not in st.session_state:
    st.session_state.temperature = 0.7

if "top_p" not in st.session_state:
    st.session_state.top_p = 0.9

if "top_k" not in st.session_state:
    st.session_state.top_k = 40

if "max_tokens" not in st.session_state:
    st.session_state.max_tokens = 1024

# Create Gemini Chat
if "chat" not in st.session_state:
    try:
        st.session_state.chat = create_chat(
            temperature=st.session_state.temperature,
            top_p=st.session_state.top_p,
            top_k=st.session_state.top_k,
            max_tokens=st.session_state.max_tokens,
        )
    except Exception as e:
        st.error(f"Failed to initialize Gemini: {e}")
        st.stop()

# ================= Top Bar =================
c1, c2, c3, c4 = st.columns([8, 1, 1, 1])

with c1:
    col1, col2 = st.columns([5, 1.5])

    col1.markdown(f"### {st.session_state.selected_model}")

    with col2:
        with st.popover("Models"):
            st.radio(
                "Select Model",
                [
                    "Gemini 3.1 Flash Lite",
                    "Gemini 2.5 Pro",
                    "Gemini 2.5 Flash Lite",
                    "Gemini 2.5 Flash",
                ],
                key="selected_model",
            )

with c2:
    with st.popover("⚙"):
        st.subheader("🎛️ Generation Settings")

        st.session_state.temperature = st.slider(
            "Temperature",
            0.0,
            2.0,
            st.session_state.temperature,
        )

        st.session_state.top_p = st.slider(
            "Top P",
            0.0,
            1.0,
            st.session_state.top_p,
        )

        st.session_state.top_k = st.slider(
            "Top K",
            1,
            100,
            st.session_state.top_k,
        )

        st.session_state.max_tokens = st.slider(
            "Maximum Output Tokens",
            128,
            4096,
            st.session_state.max_tokens,
        )

with c3:
    st.button("🔔")

with c4:
    st.button("👤")

st.divider()

# ================= Sidebar =================
with st.sidebar:

    st.title("🤖 Neha AI Studio")
    st.caption("v2.4 Pro")

    if st.button("➕ New Chat", use_container_width=True):

        st.session_state.page = "chat"
        st.session_state.current_chat_index = None
        st.session_state.messages = []

        st.session_state.chat = create_chat(
            temperature=st.session_state.temperature,
            top_p=st.session_state.top_p,
            top_k=st.session_state.top_k,
            max_tokens=st.session_state.max_tokens,
        )

        st.rerun()

    if st.button("📊 Analytics", use_container_width=True):

        if st.session_state.page == "analytics":
            st.session_state.page = "chat"
        else:
            st.session_state.page = "analytics"

        st.rerun()

    search = st.text_input(
        "",
        placeholder="🔍 Search History",
    )

    if st.button("🗑️ Clear All", use_container_width=True):

        st.session_state.chat_history = []
        save_history(st.session_state.chat_history)

        st.session_state.messages = []

        st.session_state.chat = create_chat(
            temperature=st.session_state.temperature,
            top_p=st.session_state.top_p,
            top_k=st.session_state.top_k,
            max_tokens=st.session_state.max_tokens,
        )

        st.rerun()

    st.subheader("🕒 Recent Chats")

    history = list(reversed(st.session_state.chat_history))

    for i, chat in enumerate(history):

        chat_index = len(st.session_state.chat_history) - 1 - i

        #col1, col2 = st.columns([9, 1])
        col1, col2 = st.columns([15, 1], vertical_alignment="center")

        title = chat["title"]

        if len(title) > 28:
            title = title[:28] + "..."

        with col1:
            st.button(
                f"💬 {title}",
                key=f"history_{chat_index}",
                use_container_width=True,
            )
            st.session_state.messages = chat["messages"].copy()
            st.rerun()

        with col2:
            with st.popover("⋮"):

                if st.button(
                    "✏️ Rename",
                    key=f"rename_{chat_index}",
                    use_container_width=True,
                ):
                    st.session_state.rename_index = chat_index

                if st.button(
                    "🗑 Delete",
                    key=f"delete_{chat_index}",
                    use_container_width=True,
                ):
                    del st.session_state.chat_history[chat_index]
                    save_history(st.session_state.chat_history)
                    st.rerun()

# ================= Main =================
if st.session_state.page == "chat":

    # Welcome Screen
    if len(st.session_state.messages) == 0:

        st.title("Welcome to AI Chat Assistant")
        st.caption(
            "Ask anything and receive intelligent responses powered by Gemini. "
            "Explore possibilities from coding to creative writing."
        )

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                "🐍 Explain Python Decorators",
                use_container_width=True
            ):
                st.session_state.selected_prompt = (
                    "Explain Python decorators."
                )

            if st.button(
                "📚 Summarize Machine Learning",
                use_container_width=True
            ):
                st.session_state.selected_prompt = (
                    "Summarize machine learning."
                )

            if st.button(
                "😂 Tell me a Joke",
                use_container_width=True
            ):
                st.session_state.selected_prompt = (
                    "Tell me a joke."
                )

        with col2:

            if st.button(
                "💻 Generate HTML Code",
                use_container_width=True
            ):
                st.session_state.selected_prompt = (
                    "Generate HTML code."
                )

            if st.button(
                "🗄 SQL JOIN Example",
                use_container_width=True
            ):
                st.session_state.selected_prompt = (
                    "Write a SQL JOIN example."
                )

            if st.button(
                "🐳 Explain Docker",
                use_container_width=True
            ):
                st.session_state.selected_prompt = (
                    "Explain Docker."
                )

    # ================= Chat History =================

    for i, message in enumerate(st.session_state.messages):

        avatar = "🧑" if message["role"] == "user" else "🤖"

        with st.chat_message(message["role"], avatar=avatar):

            st.markdown(message["message"])

            # Assistant Action Buttons
            if message["role"] == "assistant":

                c1, c2, c3, c4, c5, c6 = st.columns(
                    [0.6, 0.6, 0.6, 0.6, 0.6, 7]
                )

                # Copy
                with c1:
                    copy_button(message["message"])

                # Summarize
                with c2:

                    if st.button(
                        ":material/summarize:",
                        key=f"summary_btn_{i}"
                    ):

                        summary = ""

                        with st.spinner("Summarizing..."):

                            for chunk in stream_response(
                                st.session_state.chat,
                                f"Summarize the following:\n\n{message['message']}"
                            ):
                                summary += chunk

                        st.session_state[f"summary_{i}"] = summary

                # Regenerate
                with c3:

                    st.button(
                        ":material/refresh:",
                        key=f"regen_{i}",
                        help="Regenerate"
                    )

                # Like
                with c4:

                    st.button(
                        ":material/thumb_up:",
                        key=f"like_{i}",
                        help="Like"
                    )

                # Dislike
                with c5:

                    st.button(
                        ":material/thumb_down:",
                        key=f"dislike_{i}",
                        help="Dislike"
                    )

                # Show Summary
                if f"summary_{i}" in st.session_state:

                    st.info(
                        st.session_state[f"summary_{i}"]
                    )

# ================= Chat Input =================

chat = st.chat_input(
    "🔍 Ask anything...",
    accept_file=True,
    file_type=[
        "png", "jpg", "jpeg",
        "mp4", "mov", "avi", "mkv", "webm"
    ]
)

prompt = None
image = None
video = None
url = None

if chat:

    prompt = chat.text

    # Automatically detect a URL in the prompt
    if prompt:
        match = re.search(r'https?://\S+', prompt)
        if match:
            url = match.group(0)

    if chat.files:

        uploaded_file = chat.files[0]

        # Save uploaded file temporarily
        suffix = os.path.splitext(uploaded_file.name)[1]

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as tmp:

            tmp.write(uploaded_file.read())
            temp_path = tmp.name

        if uploaded_file.type.startswith("image"):
            image = temp_path

        elif uploaded_file.type.startswith("video"):
            video = temp_path


# Quick Prompt Buttons
if "selected_prompt" in st.session_state:
    prompt = st.session_state.pop("selected_prompt")


# ================= Send Message =================

if prompt or url or image or video:

    with st.chat_message("user", avatar="🧑"):

        if image:
            st.image(image, width=250)

        if video:
            st.video(video)

        if url:
            st.markdown(f"🔗 {url}")

        if prompt:
            st.markdown(prompt)

    # Save user message
    parts = []

    if prompt:
        parts.append(prompt)

    # if url:
    #     parts.append(f"URL: {url}")

    if image:
        parts.append("[Image]")

    if video:
        parts.append("[Video]")

    user_message = "\n".join(parts)

    add_message(
    st.session_state.messages,
    "user",
    user_message
    )

    # Chat Title
    title = prompt if prompt else "Media Chat"

    if len(title) > 30:
        title = title[:30] + "..."

    if st.session_state.current_chat_index is None:

        st.session_state.chat_history.append(
            {
                "title": title,
                "messages": []
            }
        )

        st.session_state.current_chat_index = (
            len(st.session_state.chat_history) - 1
        )

    st.session_state.chat_history[
        st.session_state.current_chat_index
    ]["messages"] = st.session_state.messages.copy()

    save_history(st.session_state.chat_history)

    # ================= Assistant =================

    with st.chat_message("assistant", avatar="🤖"):

        placeholder = st.empty()

        full_response = ""

        try:
             # Build the prompt that will be sent to Gemini
            ai_prompt = prompt or ""

            if url:
                ai_prompt += f"\n\nURL:\n{url}"

            with st.spinner("Thinking..."):

                for chunk in stream_response(
                    st.session_state.chat,
                    ai_prompt,
                    image=image,
                    video=video,
                ):

                    full_response += chunk

                    placeholder.markdown(
                        full_response + "▌"
                    )

            placeholder.markdown(full_response)

            add_message(
                st.session_state.messages,
                "assistant",
                full_response
            )

            st.session_state.chat_history[
                st.session_state.current_chat_index
            ]["messages"] = (
                st.session_state.messages.copy()
            )

            save_history(
                st.session_state.chat_history
            )

            st.rerun()

        except Exception as e:

            st.error(f"Error: {e}")

        finally:

            # Delete temporary files
            if image and os.path.exists(image):
                os.remove(image)

            if video and os.path.exists(video):
                os.remove(video)


# ================= Analytics =================

if st.session_state.page == "analytics":

    st.title("📊 Conversation Analytics")

    stats = conversation_stats(
        st.session_state.messages
    )

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "💬 Total Messages",
            stats["Total Messages"]
        )

        st.metric(
            "👤 User Messages",
            stats["User Messages"]
        )

        st.metric(
            "🤖 AI Messages",
            stats["AI Messages"]
        )

    with col2:

        st.metric(
            "📝 Total Words",
            stats["Total Words"]
        )

        st.metric(
            "⏱ Duration",
            stats["Conversation Duration"]
        )

