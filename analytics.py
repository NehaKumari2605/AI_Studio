import streamlit as st
import pandas as pd
from database import dashboard_stats

#  ================= Analytics =================
def show_analytics(user_id):

    st.title("📊 Conversation Analytics")
    st.caption("Overview of your AI chat activity")

    stats = dashboard_stats(st.session_state.user_id)

    c1, c2, c3 = st.columns(3)

    with c1:
        with st.container(border=True):
            st.metric(
                "💬 Total Messages",
                stats["total_messages"]
            )

    with c2:
        with st.container(border=True):
            st.metric(
                "👤 User Messages",
                stats["user_messages"]
            )

    with c3:
        with st.container(border=True):
            st.metric(
                "🤖 AI Messages",
                stats["ai_messages"]
            )

    st.write("")

    c1, c2, c3 = st.columns(3)

    with c1:
        with st.container(border=True):
            st.metric(
                "📝 Total Words",
                stats["total_words"]
            )

    with c2:
        with st.container(border=True):
            st.metric(
                "💬 Conversations",
                stats["total_conversations"]
            )

    with c3:
        with st.container(border=True):
            st.metric(
                "⏱ Duration",
                stats["conversation_duration"]
            )

    st.write("")

    # ================= Activity =================

    with st.container(border=True):

        st.subheader("📈 Activity Summary")

        total = max(stats["total_messages"], 1)

        user_percent = round(
            stats["user_messages"] / total * 100
        )

        ai_percent = round(
            stats["ai_messages"] / total * 100
        )

        st.progress(stats["user_messages"] / total)

        st.write(f"👤 User Messages : **{user_percent}%**")
        st.write(f"🤖 AI Messages : **{ai_percent}%**")

    st.write("")