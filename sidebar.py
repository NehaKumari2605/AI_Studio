import streamlit as st
from chatbot import create_chat, change_chat
import time

from database import (
    get_conversations,
    get_messages,
    rename_conversation,
    delete_conversation,
    delete_all_conversations,
    pin_conversation,
)
from utils import (
    export_pdf,
    export_docx,
    export_txt,
    export_md,
    export_json,
)

def show_sidebar(cookies):
    with st.sidebar:

        st.title("🤖 AI ChatBot")
        st.caption("v2.4 Pro")

        if st.button(":material/chat_add_on: New Chat", use_container_width=True):
        

            st.session_state.page = "chat"

            st.session_state.current_conversation = None
            st.session_state.messages = []
            st.session_state.chat = create_chat(
                model_name=st.session_state.selected_model,
                temperature=st.session_state.temperature,
                top_p=st.session_state.top_p,
                top_k=st.session_state.top_k,
                max_tokens=st.session_state.max_tokens,
                web_search=st.session_state.web_search,
            )

            st.rerun()

        if st.button(":material/analytics: Analytics", use_container_width=True):
            if st.session_state.page == "analytics":
                st.session_state.page = "chat"
            else:
                st.session_state.page = "analytics"

            st.rerun()

        with st.popover(":material/delete: Clear Chat", use_container_width=True):

            st.warning("Delete all conversations?")

            if st.button(
                "✅ Yes, Delete All",
                use_container_width=True,
                key="delete_all_confirm",
            ):

                delete_all_conversations(st.session_state.user_id)

                st.session_state.current_conversation = None
                st.session_state.messages = []
                st.session_state.page = "chat"

                st.session_state.chat = create_chat(
                    model_name=st.session_state.selected_model,
                    temperature=st.session_state.temperature,
                    top_p=st.session_state.top_p,
                    top_k=st.session_state.top_k,
                    max_tokens=st.session_state.max_tokens,
                    web_search=st.session_state.web_search,
                )

                st.rerun()

            if st.button(
                "❌ Cancel",
                use_container_width=True,
                key="delete_all_cancel",
            ):
                st.rerun()

        search = st.text_input(
            "Search",
            placeholder="Search History...",
            icon=":material/search:",
            label_visibility="collapsed",
        )
        st.divider()

        st.markdown("### Recent Chats")

        conversations = []

        if st.session_state.user_id:

            conversations = get_conversations(
                st.session_state.user_id
            )

            conversations = [
                conv
                for conv in conversations
                if conv["id"] not in st.session_state.hidden_conversations
            ]

        if search:
            conversations = [
                conv for conv in conversations
                if search.lower() in conv["title"].lower()
            ]

        for conv in conversations:

            col1, col2 = st.columns([15, 1], vertical_alignment="center")

            title = conv["title"]

            if conv["pinned"]:
                title = "📌 " + title

            if len(title) > 28:
                title = title[:28] + "..."

            with col1:
                if st.button(
                    title,
                    key=f"history_{conv['id']}",
                    use_container_width=True,
                ):
                    st.session_state.page = "chat" 
                    st.session_state.current_conversation = conv["id"]

                    st.session_state.messages = get_messages(
                        conv["id"]
                    )

                    st.session_state.chat = create_chat(
                        model_name=st.session_state.selected_model,
                        temperature=st.session_state.temperature,
                        top_p=st.session_state.top_p,
                        top_k=st.session_state.top_k,
                        max_tokens=st.session_state.max_tokens,
                        web_search=st.session_state.web_search,
                    )

                    st.rerun()

            with col2:
                with st.popover("⋮"):
                    if conv["pinned"]:
                        if st.button(
                            ":material/keep_off: Unpin",
                            key=f"unpin_{conv['id']}",
                            use_container_width=True,
                        ):
                            pin_conversation(conv["id"], False)
                            st.rerun()
                    else:
                        if st.button(
                            ":material/keep: Pin",
                            key=f"pin_{conv['id']}",
                            use_container_width=True,
                        ):
                            pin_conversation(conv["id"], True)
                            st.rerun()

                    with st.popover(":material/edit: Rename", use_container_width=True):

                        new_title = st.text_input(
                            "New conversation name",
                            value=conv["title"],
                            key=f"rename_input_{conv['id']}"
                        )

                        col1, col2 = st.columns(2)

                        with col1:
                            if st.button(
                                "✅  Save",
                                key=f"save_{conv['id']}",
                                use_container_width=True,
                            ):
                                rename_conversation(conv["id"], new_title)
                                st.toast("✅ Conversation renamed!")
                                st.rerun()

                        with col2:
                            if st.button(
                                "❌ Cancel",
                                key=f"cancel_{conv['id']}",
                                use_container_width=True,
                            ):
                                st.rerun()

                    with st.popover("🗑 Delete", use_container_width=True):

                        st.warning("Delete this conversation?")

                        if st.button(
                            "✅ Yes, Delete",
                            key=f"confirm_delete_{conv['id']}",
                            use_container_width=True,
                        ):
                            delete_conversation(conv["id"])

                            if st.session_state.current_conversation == conv["id"]:
                                st.session_state.current_conversation = None
                                st.session_state.messages = []

                            st.rerun()

                        if st.button(
                            "❌ Cancel",
                            key=f"cancel_delete_{conv['id']}",
                            use_container_width=True,
                        ):
                            st.rerun()

                    with st.popover(":material/download: Export Chat", use_container_width=True):

                        export_format = st.radio(
                            "Export As",
                            [
                                "PDF",
                                "DOCX",
                                "TXT",
                                "Markdown",
                                "JSON"
                            ],
                            key=f"export_format_{conv['id']}",
                        )

                        messages = get_messages(conv["id"])

                        if export_format == "PDF":
                            data = export_pdf(messages)
                            filename = "chat.pdf"
                            mime = "application/pdf"

                        elif export_format == "DOCX":
                            data = export_docx(messages)
                            filename = "chat.docx"
                            mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

                        elif export_format == "TXT":
                            data = export_txt(messages)
                            filename = "chat.txt"
                            mime = "text/plain"

                        elif export_format == "Markdown":
                            data = export_md(messages)
                            filename = "chat.md"
                            mime = "text/markdown"

                        else:
                            data = export_json(messages)

                            filename = "chat.json"
                            mime = "application/json"

                        st.download_button(
                            "⬇ Download",
                            data=data,
                            file_name=filename,
                            mime=mime,
                            use_container_width=True,
                            key=f"download_{conv['id']}"
                        )

        st.divider()
        with st.container(border=True):
            col1, col2 = st.columns([5,1])
            with col1:
                st.write(f"👤 **{st.session_state.user_name}**")

            with col2:

                    with st.popover(":material/settings:"):

                        with st.popover("🤖 Model", use_container_width=True):
                            st.radio(
                                "Choose AI Model",
                                [
                                    "Gemini 3.1 Flash Lite",
                                    "Gemini 2.5 Flash Lite",
                                    "Gemini 2.5 Flash",
                                    "Gemini 2.5 Pro",
                                ],
                                key="selected_model",
                                on_change=change_chat,
                            )

                        with st.popover(":material/tune: Generation", use_container_width=True):

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

                            if st.button("Apply Settings", use_container_width=True):
                                change_chat()
                                st.success("Settings applied.")

                        with st.popover(":material/logout: Logout", use_container_width=True):

                            st.warning("⚠️ Are you sure you want to logout?")

                            if st.button("✅ Yes, Logout", use_container_width=True):

                                cookies["user_id"] = ""
                                cookies["user_name"] = ""
                                cookies.save()

                                st.session_state.logged_in = False
                                st.session_state.user = None
                                st.session_state.user_id = None
                                st.session_state.user_name = ""
                                st.session_state.current_conversation = None
                                st.session_state.messages = []
                                st.session_state.auth_page = "login"

                                st.success("✅ Successfully logged out!")
                                time.sleep(1)
                                st.rerun()

                            if st.button("❌ Cancel", use_container_width=True):
                                st.session_state.page = "chat"
                                st.rerun()