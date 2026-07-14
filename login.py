import streamlit as st

#===============show login=================
def show_login(login_user, cookies):
        st.markdown("""
            <h1 style="color:black;">🤖 AI ChatBot</h1>
            <p style="color:black;">Welcome back! Please sign in.</p>
            """, unsafe_allow_html=True)

        email = st.text_input("Email")

        password = st.text_input(
            "Password",
            type="password"
        )

        if st.button("Login", use_container_width=True):

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

        st.write("Don't have an account?")

        if st.button("Register Here", use_container_width=True):
            st.session_state.auth_page = "register"
            st.rerun()


#=================show register==========================
def show_register(register_user):
        st.title(" Register")

        name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")

        if st.button("Create Account", use_container_width=True):

            if not name.strip() or not email.strip() or not password or not confirm:
                st.error("⚠️ Please fill all required fields.")

            elif password != confirm:
                st.error("⚠️ Passwords do not match.")

            else:
                success, message = register_user(
                    name,
                    email,
                    password
                )

                if success:
                    st.success(message)
                    st.session_state.auth_page = "login"
                    st.rerun()
                else:
                    st.error(message)

        if st.button("Back to Login", use_container_width=True):
            st.session_state.auth_page = "login"
            st.rerun()

        if not st.session_state.logged_in:
            st.stop()