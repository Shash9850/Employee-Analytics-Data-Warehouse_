
"""Reusable login and logout interface for the Streamlit application."""

import streamlit as st

from utils.auth import authenticate, logout


def render_login():
    """Render the login screen and authenticate submitted credentials."""
    st.markdown(
        """
        <style>
        .login-header {
            text-align: center;
            padding: 1.5rem 0 0.5rem 0;
        }
        .login-subtitle {
            color: #64748b;
            text-align: center;
            margin-bottom: 1.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _, center, _ = st.columns([1, 1.2, 1])

    with center:
        st.markdown(
            """
            <div class="login-header">
                <h1>Employee Analytics DW</h1>
            </div>
            <div class="login-subtitle">
                Sign in to access workforce intelligence
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            username = st.text_input("Username", max_chars=100)
            password = st.text_input(
                "Password",
                type="password",
                max_chars=1024,
            )
            submitted = st.form_submit_button(
                "Sign in",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            if not username.strip() or not password:
                st.error("Enter both your username and password.")
                return

            try:
                user = authenticate(username, password)
            except RuntimeError:
                st.error(
                    "Login is temporarily unavailable. "
                    "Please check the database connection and try again."
                )
                return

            if user is None:
                st.error("Invalid username or password.")
                return

            st.session_state["auth_user"] = user
            st.rerun()


def render_user_sidebar():
    """Show the logged-in user and a logout control in the sidebar."""
    user = st.session_state.get("auth_user")

    if not user:
        return

    with st.sidebar:
        st.divider()
        st.caption("SIGNED IN AS")
        st.write(f"**{user['username']}**")
        st.caption(f"Role: {user['role']}")

        if st.button("Log out", use_container_width=True):
            logout()
