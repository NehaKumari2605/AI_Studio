import streamlit as st


def _inject_auth_css():
    """Inject premium white-theme CSS for login & register pages."""
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        /* ─── Page background ─── */
        [data-testid="stApp"] {
            background: linear-gradient(160deg, #f0f4ff 0%, #eef2ff 55%, #faf5ff 100%) !important;
        }
        header[data-testid="stHeader"] { background: transparent !important; }
        footer { visibility: hidden !important; }
        #MainMenu { visibility: hidden !important; }
        section[data-testid="stSidebar"] { display: none !important; }
        [data-testid="stToolbar"] { display: none !important; }
        [data-testid="stDecoration"] { display: none !important; }

        /* ─── Font base ─── */
        [data-testid="stApp"],
        [data-testid="stApp"] * {
            font-family: 'Inter', sans-serif !important;
        }

        /* ─── Constrain main block width & center ─── */
        [data-testid="stMainBlockContainer"] {
            max-width: 460px !important;
            margin: 0 auto !important;
            padding-top: 36px !important;
        }

        /* ─── THE CARD: target the stVerticalBlock that holds everything ─── */
        [data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] {
            background: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 24px !important;
            padding: 36px 32px 28px 32px !important;
            box-shadow:
                0 1px 3px rgba(0,0,0,0.04),
                0 10px 32px rgba(0,0,0,0.06),
                0 0 0 1px rgba(99,102,241,0.03) !important;
        }

        /* ─── Reset ALL inner wrappers so nothing creates sub-cards ─── */
        [data-testid="stMainBlockContainer"] [data-testid="stVerticalBlockBorderWrapper"] {
            background: transparent !important;
            border: none !important;
            border-radius: 0 !important;
            padding: 0 !important;
            box-shadow: none !important;
        }

        /* ─── Brand header ─── */
        .auth-brand {
            text-align: center;
            margin-bottom: 24px;
        }
        .auth-brand .icon-wrap {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 60px; height: 60px;
            border-radius: 18px;
            background: linear-gradient(135deg, #eef2ff, #f5f3ff);
            border: 1px solid #e0e7ff;
            font-size: 28px;
            margin-bottom: 14px;
            box-shadow: 0 4px 14px rgba(99,102,241,0.1);
        }
        .auth-brand h1 {
            font-size: 1.55rem !important;
            font-weight: 800 !important;
            color: #0f172a !important;
            margin: 0 0 4px 0 !important;
            letter-spacing: -0.5px !important;
        }
        .auth-brand p {
            font-size: 0.88rem !important;
            color: #64748b !important;
            margin: 0 !important;
            font-weight: 400 !important;
        }

        /* ─── Form labels ─── */
        [data-testid="stWidgetLabel"] p {
            font-size: 0.84rem !important;
            font-weight: 600 !important;
            color: #334155 !important;
        }

        /* ─── Text inputs ─── */
        div[data-baseweb="input"] {
            background: #f8fafc !important;
            border: 1.5px solid #e2e8f0 !important;
            border-radius: 10px !important;
            transition: border-color 0.2s, box-shadow 0.2s !important;
        }
        div[data-baseweb="input"]:focus-within {
            border-color: #6366f1 !important;
            box-shadow: 0 0 0 3px rgba(99,102,241,0.12) !important;
            background: #ffffff !important;
        }
        div[data-baseweb="input"] input {
            font-size: 0.92rem !important;
            color: #0f172a !important;
        }
        div[data-baseweb="input"] input::placeholder {
            color: #94a3b8 !important;
        }

        /* ─── ALL buttons base ─── */
        [data-testid="stMainBlockContainer"] button {
            border-radius: 10px !important;
            height: 44px !important;
            font-size: 0.92rem !important;
            font-weight: 600 !important;
            cursor: pointer !important;
            transition: transform 0.15s ease, box-shadow 0.2s ease, background 0.15s ease !important;
        }

        /* ─── Primary button (type=primary from Streamlit) ─── */
        [data-testid="stMainBlockContainer"] button[kind="primary"],
        [data-testid="stMainBlockContainer"] button[data-testid="stBaseButton-primary"] {
            background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%) !important;
            color: #ffffff !important;
            border: none !important;
            letter-spacing: 0.2px !important;
            box-shadow: 0 4px 14px -2px rgba(79,70,229,0.45) !important;
        }
        [data-testid="stMainBlockContainer"] button[kind="primary"]:hover,
        [data-testid="stMainBlockContainer"] button[data-testid="stBaseButton-primary"]:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 20px -2px rgba(79,70,229,0.55) !important;
        }
        [data-testid="stMainBlockContainer"] button[kind="primary"]:active,
        [data-testid="stMainBlockContainer"] button[data-testid="stBaseButton-primary"]:active {
            transform: translateY(0) !important;
        }

        /* ─── Secondary button ─── */
        [data-testid="stMainBlockContainer"] button[kind="secondary"],
        [data-testid="stMainBlockContainer"] button[data-testid="stBaseButton-secondary"] {
            background: #ffffff !important;
            color: #4f46e5 !important;
            border: 1.5px solid #c7d2fe !important;
            box-shadow: none !important;
        }
        [data-testid="stMainBlockContainer"] button[kind="secondary"]:hover,
        [data-testid="stMainBlockContainer"] button[data-testid="stBaseButton-secondary"]:hover {
            background: #eef2ff !important;
            border-color: #818cf8 !important;
        }

        /* ─── Divider ─── */
        .auth-divider {
            display: flex;
            align-items: center;
            margin: 18px 0;
            font-size: 0.72rem;
            font-weight: 600;
            color: #94a3b8;
            letter-spacing: 0.8px;
        }
        .auth-divider::before,
        .auth-divider::after {
            content: '';
            flex: 1;
            height: 1px;
            background: #e2e8f0;
        }
        .auth-divider::before { margin-right: 12px; }
        .auth-divider::after  { margin-left: 12px;  }

        /* ─── Footer ─── */
        .auth-footer {
            text-align: center;
            margin-top: 16px;
            font-size: 0.78rem;
            color: #94a3b8;
        }
        </style>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────
# LOGIN
# ──────────────────────────────────────────────
def show_login(login_user, cookies):
    _inject_auth_css()

    st.markdown("""
        <div class="auth-brand">
            <div class="icon-wrap">🤖</div>
            <h1>AI Studio</h1>
            <p>Welcome back — sign in to continue</p>
        </div>
    """, unsafe_allow_html=True)

    email = st.text_input("Email", placeholder="name@example.com")
    password = st.text_input("Password", type="password", placeholder="••••••••")

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    if st.button("Sign In", use_container_width=True, type="primary"):
        if not email.strip() or not password.strip():
            st.error("⚠️ Please fill all required fields.")
        else:
            success, result = login_user(email, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.user = result
                st.session_state.user_id = result["id"]
                st.session_state.user_name = result["full_name"]
                cookies["user_id"] = str(result["id"])
                cookies["user_name"] = result["full_name"]
                cookies.save()
                st.success("✅ Login Successful")
                st.rerun()
            else:
                st.error(result)

    st.markdown('<div class="auth-divider">OR</div>', unsafe_allow_html=True)

    if st.button("Create an Account", use_container_width=True):
        st.session_state.auth_page = "register"
        st.rerun()

    st.markdown(
        '<div class="auth-footer">Secure login powered by AI Studio</div>',
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────
# REGISTER
# ──────────────────────────────────────────────
def show_register(register_user):
    _inject_auth_css()

    st.markdown("""
        <div class="auth-brand">
            <div class="icon-wrap">✨</div>
            <h1>Create Account</h1>
            <p>Join AI Studio — your personal AI assistant</p>
        </div>
    """, unsafe_allow_html=True)

    name = st.text_input("Full Name", placeholder="Jane Doe")
    email = st.text_input("Email", placeholder="name@example.com")
    password = st.text_input("Password", type="password", placeholder="••••••••")
    confirm = st.text_input("Confirm Password", type="password", placeholder="••••••••")

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    if st.button("Register Account", use_container_width=True, type="primary"):
        if not name.strip() or not email.strip() or not password or not confirm:
            st.error("⚠️ Please fill all required fields.")
        elif password != confirm:
            st.error("⚠️ Passwords do not match.")
        else:
            success, message = register_user(name, email, password)
            if success:
                st.success(message)
                st.session_state.auth_page = "login"
                st.rerun()
            else:
                st.error(message)

    st.markdown(
        '<div class="auth-divider">ALREADY HAVE AN ACCOUNT?</div>',
        unsafe_allow_html=True,
    )

    if st.button("Back to Login", use_container_width=True):
        st.session_state.auth_page = "login"
        st.rerun()