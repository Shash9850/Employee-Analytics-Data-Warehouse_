
"""Role-based navigation controller for Employee Analytics DW."""

import streamlit as st

from utils.auth import (
    has_permission,
    require_login,
)
from utils.login_ui import render_login, render_user_sidebar

st.set_page_config(
    page_title="Employee Analytics DW",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Authenticate before showing application pages.
if not st.session_state.get("auth_user"):
    # Hide Streamlit's sidebar and its expand control before login.
    st.markdown(
        """
        <style>
            section[data-testid="stSidebar"] {
                display: none !important;
            }

            button[data-testid="stSidebarCollapsedControl"] {
                display: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    render_login()
    st.stop()


require_login()
render_user_sidebar()

# Each page is shown only when the user's role has its permission.
pages = {
    "Home": [st.Page("home.py", title="Home", icon="🏠", default=True),

    ],
    "Workforce": [
        st.Page(
            "pages/Employee_onboarding.py",
            title="Employee Onboarding",
            icon="📊",
        ),
        st.Page(
            "pages/Employee_360.py",
            title="Employee 360",
            icon="🏠",
        ),
        st.Page(
            "pages/Department_update.py",
            title="Department Update",
            icon="➕",
        ),
    ],
    "Analytics": [
        st.Page(
            "pages/dashboard.py",
            title="Dashboard",
            icon="👤",
        ),
        st.Page(
            "pages/Performance_Reviews.py",
            title="Performance Reviews",
            icon="🏢",
        ),
        st.Page(
            "pages/projects.py",
            title="Projects",
            icon="📈",
        ),
    ],
}



# User Management is available only to Admin.
if has_permission("manage_users"):
    pages["Administration"] = [
        st.Page(
            "pages/User_management.py",
            title="User Management",
            icon="⭐",
        ),
    ]

navigation = st.navigation(pages)
navigation.run()
