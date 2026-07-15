import streamlit as st
import time
from datetime import datetime, date, timedelta
from chatbot import create_chat, change_chat
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


def _categorize_recent_chats(convs):
    today = date.today()
    yesterday = today - timedelta(days=1)
    seven_days_ago = today - timedelta(days=7)

    groups = {
        "Today": [],
        "Yesterday": [],
        "Previous 7 Days": [],
        "Older": []
    }

    for conv in convs:
        created = conv.get("created_at")
        if isinstance(created, datetime):
            c_date = created.date()
        elif isinstance(created, date):
            c_date = created
        else:
            c_date = today

        if c_date == today:
            groups["Today"].append(conv)
        elif c_date == yesterday:
            groups["Yesterday"].append(conv)
        elif c_date >= seven_days_ago:
            groups["Previous 7 Days"].append(conv)
        else:
            groups["Older"].append(conv)

    return {group_name: items for group_name, items in groups.items() if items}


def show_sidebar(cookies):
    with st.sidebar:
        # Header Branding
        st.markdown("""
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                <div style="font-size: 24px; line-height: 1;">✨</div>
                <div>
                    <h2 style="font-size: 1.15rem; font-weight: 800; margin: 0; color: #0f172a;">AI Studio</h2>
                    <span style="font-size: 0.72rem; font-weight: 600; background: #e0e7ff; color: #4338ca; padding: 1px 7px; border-radius: 10px;">Pro 3.1</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # New Chat Primary Button
        st.markdown('<div class="new-chat-btn">', unsafe_allow_html=True)
        if st.button("➕ New Chat", use_container_width=True):
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
        st.markdown('</div>', unsafe_allow_html=True)

        # Quick View Navigation (Chat / Analytics)
        c1, c2 = st.columns(2)
        with c1:
            chat_btn_type = "primary" if st.session_state.page == "chat" else "secondary"
            if st.button("💬 Chat", use_container_width=True, type=chat_btn_type):
                st.session_state.page = "chat"
                st.rerun()
        with c2:
            analytics_btn_type = "primary" if st.session_state.page == "analytics" else "secondary"
            if st.button("📊 Stats", use_container_width=True, type=analytics_btn_type):
                st.session_state.page = "analytics"
                st.rerun()

        # Search Bar
        search = st.text_input(
            "Search History",
            placeholder="🔍 Search conversations...",
            label_visibility="collapsed",
        )

        st.divider()

        # Fetch Conversations
        conversations = []
        if st.session_state.user_id:
            conversations = get_conversations(st.session_state.user_id)
            conversations = [
                conv for conv in conversations
                if conv["id"] not in st.session_state.hidden_conversations
            ]

        if search:
            conversations = [
                conv for conv in conversations
                if search.lower() in conv["title"].lower()
            ]

        # Pinned Conversations Group
        pinned_convs = [c for c in conversations if c["pinned"]]
        recent_convs = [c for c in conversations if not c["pinned"]]

        if pinned_convs:
            st.markdown(f"""
                <div class="sidebar-section-header">
                    <span>📌 Pinned</span>
                    <span class="sidebar-badge">{len(pinned_convs)}</span>
                </div>
            """, unsafe_allow_html=True)
            for conv in pinned_convs:
                _render_conv_item(conv)
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        if not conversations:
            st.markdown("""
                <div class="sidebar-section-header">
                    <span>💬 Recent Chats</span>
                </div>
            """, unsafe_allow_html=True)
            st.caption("No conversations yet. Start a new chat!")
        else:
            categorized = _categorize_recent_chats(recent_convs)
            for timeframe, conv_list in categorized.items():
                st.markdown(f"""
                    <div class="sidebar-section-header">
                        <span>{timeframe}</span>
                        <span class="sidebar-badge">{len(conv_list)}</span>
                    </div>
                """, unsafe_allow_html=True)
                for conv in conv_list:
                    _render_conv_item(conv)

        st.divider()

        # Footer User & Settings Section
        st.markdown('<div class="sidebar-user-footer-card">', unsafe_allow_html=True)
        c1, c2 = st.columns([5, 1], vertical_alignment="center")
        with c1:
            initial = st.session_state.user_name[:1].upper() if st.session_state.user_name else 'U'
            st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 10px; padding: 2px 0;">
                    <div style="width: 32px; height: 32px; min-width: 32px; border-radius: 50%; background: linear-gradient(135deg, #6366f1, #a855f7); color: white; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 14px; box-shadow: 0 2px 6px rgba(99, 102, 241, 0.25);">
                        {initial}
                    </div>
                    <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        <div style="font-weight: 700; font-size: 0.9rem; color: #0f172a;">{st.session_state.user_name}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with c2:
            with st.popover("⚙️"):
                st.markdown("### ⚙️ Settings")

                st.markdown("#### 🤖 AI Model")

                def _on_sidebar_model_change():
                    st.session_state.selected_model = st.session_state.sidebar_selected_model
                    change_chat()

                model_options = [
                    "Gemini 3.1 Flash Lite",
                    "Gemini 2.5 Flash Lite",
                    "Gemini 2.5 Flash",
                    "Gemini 2.5 Pro",
                ]
                current_idx = model_options.index(st.session_state.selected_model) if st.session_state.selected_model in model_options else 0

                st.radio(
                    "Model",
                    model_options,
                    index=current_idx,
                    key="sidebar_selected_model",
                    on_change=_on_sidebar_model_change,
                    label_visibility="collapsed",
                )

                st.markdown("#### 🎛️ Parameters")
                st.session_state.temperature = st.slider(
                    "Creativity (Temperature)",
                    0.0, 2.0, st.session_state.temperature
                )
                st.session_state.max_tokens = st.slider(
                    "Max Tokens",
                    128, 4096, st.session_state.max_tokens
                )

                st.divider()

                with st.popover("🗑 Clear All History", use_container_width=True):
                    st.warning("Delete all conversations?")
                    if st.button("✅ Confirm Delete All", use_container_width=True, key="del_all_confirm"):
                        delete_all_conversations(st.session_state.user_id)
                        st.session_state.current_conversation = None
                        st.session_state.messages = []
                        st.session_state.page = "chat"
                        st.rerun()

                if st.button("🚪 Logout", use_container_width=True, key="sidebar_logout"):
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
                    st.success("Log out successful")
                    time.sleep(0.5)
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


def _render_conv_item(conv):
    is_active = st.session_state.current_conversation == conv["id"]
    card_class = "recent-chat-row-card active-card" if is_active else "recent-chat-row-card"

    st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
    col1, col2 = st.columns([6, 1], vertical_alignment="center")

    title = conv["title"]
    icon = "📌 " if conv["pinned"] else "💬 "
    display_title = icon + title
    if len(display_title) > 26:
        display_title = display_title[:26] + "..."

    with col1:
        if st.button(display_title, key=f"history_{conv['id']}", use_container_width=True):
            st.session_state.page = "chat"
            st.session_state.current_conversation = conv["id"]
            messages = get_messages(conv["id"])
            st.session_state.messages = messages
            st.session_state.chat = create_chat(
                model_name=st.session_state.selected_model,
                temperature=st.session_state.temperature,
                top_p=st.session_state.top_p,
                top_k=st.session_state.top_k,
                max_tokens=st.session_state.max_tokens,
                web_search=st.session_state.web_search,
                messages=messages,
            )
            st.rerun()

    with col2:
        with st.popover("⋮"):
            # Pin / Unpin
            if conv["pinned"]:
                if st.button("📌 Unpin", key=f"unpin_{conv['id']}", use_container_width=True):
                    pin_conversation(conv["id"], False)
                    st.rerun()
            else:
                if st.button("📌 Pin Chat", key=f"pin_{conv['id']}", use_container_width=True):
                    pin_conversation(conv["id"], True)
                    st.rerun()

            # Rename
            with st.popover("✏️ Rename", use_container_width=True):
                new_title = st.text_input("New Name", value=conv["title"], key=f"rename_in_{conv['id']}")
                if st.button("Save", key=f"save_ren_{conv['id']}", use_container_width=True):
                    rename_conversation(conv["id"], new_title)
                    st.rerun()

            # Delete
            with st.popover("🗑 Delete", use_container_width=True):
                st.warning("Delete chat?")
                if st.button("Confirm Delete", key=f"conf_del_{conv['id']}", use_container_width=True):
                    delete_conversation(conv["id"])
                    if st.session_state.current_conversation == conv["id"]:
                        st.session_state.current_conversation = None
                        st.session_state.messages = []
                    st.rerun()

            # Export
            with st.popover("💾 Export", use_container_width=True):
                fmt = st.radio(
                    "Format",
                    ["PDF", "DOCX", "TXT", "Markdown", "JSON"],
                    key=f"exp_fmt_{conv['id']}"
                )
                messages = get_messages(conv["id"])
                if fmt == "PDF":
                    data = export_pdf(messages)
                    fn = "chat.pdf"
                    mime = "application/pdf"
                elif fmt == "DOCX":
                    data = export_docx(messages)
                    fn = "chat.docx"
                    mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                elif fmt == "TXT":
                    data = export_txt(messages)
                    fn = "chat.txt"
                    mime = "text/plain"
                elif fmt == "Markdown":
                    data = export_md(messages)
                    fn = "chat.md"
                    mime = "text/markdown"
                else:
                    data = export_json(messages)
                    fn = "chat.json"
                    mime = "application/json"

                st.download_button(
                    "⬇ Download",
                    data=data,
                    file_name=fn,
                    mime=mime,
                    use_container_width=True,
                    key=f"dl_btn_{conv['id']}"
                )

    st.markdown('</div>', unsafe_allow_html=True)