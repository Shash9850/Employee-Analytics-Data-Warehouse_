
"""Admin-only user management for the Employee Analytics platform."""

import re

import streamlit as st

from db.db_manager import DatabaseConnection
from utils.auth import ROLES, hash_password, require_permission


st.set_page_config(
    page_title="User Management",
    page_icon="🔐",
    layout="wide",
)

require_permission("manage_users")

db = DatabaseConnection()





# Load departments for account assignment.
try:
    departments = db.fetch_checked(
        """
        SELECT department_id, department_name
        FROM departments
        ORDER BY department_name
        """
    )
except RuntimeError:
    st.error("Unable to load departments from the database.")
    st.stop()

department_options = {
    row["department_name"]: row["department_id"]
    for row in departments
}






st.title("🔐 User Management")
st.caption("Create accounts, assign roles, and manage account access.")

# Load current accounts.
try:
    users = db.fetch_checked(
        """
        SELECT user_id, username, role, is_active, created_at
        FROM app_users
        ORDER BY username
        """
    )
except RuntimeError:
    st.error("Unable to load user accounts. Check the database connection.")
    st.stop()

active_count = sum(bool(user["is_active"]) for user in users)
admin_count = sum(
    user["role"] == "Admin" and bool(user["is_active"])
    for user in users
)

col1, col2, col3 = st.columns(3)
col1.metric("Total accounts", len(users))
col2.metric("Active accounts", active_count)
col3.metric("Active administrators", admin_count)

st.divider()

# Create a user account.

st.subheader("Create an account")

# Keep the role outside the form so the department field updates when the role changes.
role = st.selectbox("Role", sorted(ROLES), key="new_user_role")

department_id = None
if role == "Department Manager":
    if not department_options:
        st.error("No departments are available. Create a department first.")
        st.stop()

with st.form("create_user_form"):
    username = st.text_input(
        "Username",
        max_chars=100,
        help="Use 3–100 letters, numbers, periods, underscores, or hyphens.",
    )

    if role == "Department Manager":
        selected_department = st.selectbox(
            "Department",
            options=list(department_options.keys()),
        )
        department_id = department_options[selected_department]

    password = st.text_input(
        "Temporary password",
        type="password",
        help="At least 12 characters.",
    )
    confirm_password = st.text_input(
        "Confirm password",
        type="password",
    )
    create_submitted = st.form_submit_button(
        "Create account",
        type="primary",
    )

if create_submitted:
    username = username.strip()
    username_pattern = r"^[A-Za-z0-9_.-]{3,100}$"

    if not re.fullmatch(username_pattern, username):
        st.error(
            "Username must be 3–100 characters and contain only "
            "letters, numbers, periods, underscores, or hyphens."
        )
    elif len(password) < 12:
        st.error("Password must contain at least 12 characters.")
    elif password != confirm_password:
        st.error("The passwords do not match.")
    else:
        try:
            password_hash = hash_password(password)
        except ValueError as exc:
            st.error(str(exc))
        else:
            created = db.execute(
                """
                INSERT INTO app_users
                    (username, password_hash, role, department_id, is_active)
                VALUES (%s, %s, %s, %s, TRUE)
                """,
                (username, password_hash, role, department_id),
            )

            if created:
                st.success(
                    f"Account '{username}' created with role '{role}'."
                )
                st.rerun()
            else:
                st.error(
                    "Account creation failed. The username may already exist, "
                    "or the database may have rejected the operation."
                )


st.divider()

# Display accounts.
st.subheader("Existing accounts")

if users:
    display_users = [
        {
            "Username": user["username"],
            "Role": user["role"],
            "Status": "Active" if user["is_active"] else "Inactive",
            "Created": str(user["created_at"]),
        }
        for user in users
    ]
    st.dataframe(display_users, use_container_width=True, hide_index=True)
else:
    st.info("No user accounts were found.")

st.divider()

# Change account status.
st.subheader("Activate or deactivate an account")

eligible_users = [
    user for user in users
    if user["username"] != st.session_state["auth_user"]["username"]
]

if not eligible_users:
    st.info("There are no other accounts to manage.")
else:
    selected_username = st.selectbox(
        "Select account",
        [user["username"] for user in eligible_users],
    )

    selected_user = next(
        user for user in eligible_users
        if user["username"] == selected_username
    )

    is_active = bool(selected_user["is_active"])
    action_label = "Deactivate account" if is_active else "Reactivate account"

    if st.button(action_label):
        if is_active and selected_user["role"] == "Admin":
            if admin_count <= 1:
                st.error(
                    "You cannot deactivate the last active administrator."
                )
                st.stop()

        new_status = not is_active

        updated = db.execute(
            """
            UPDATE app_users
            SET is_active = %s
            WHERE user_id = %s
            """,
            (new_status, selected_user["user_id"]),
        )

        if updated:
            st.success(
                f"Account '{selected_username}' "
                f"{'activated' if new_status else 'deactivated'}."
            )
            st.rerun()
        else:
            st.error("The account status could not be updated.")










# ---------------------------------------------------------
# PROJECT MANAGER ASSIGNMENTS
# ---------------------------------------------------------

st.divider()
st.subheader("Project Manager Assignments")
st.caption(
    "Assign projects to Project Managers or revoke existing assignments. "
    "Project access is controlled by the project_managers mapping table."
)

try:
    project_managers = db.fetch_checked(
        """
        SELECT user_id, username
        FROM app_users
        WHERE role = 'Project Manager'
          AND is_active = TRUE
        ORDER BY username
        """
    )

    available_projects = db.fetch_checked(
        """
        SELECT project_id, project_name, department_id, status
        FROM projects
        ORDER BY project_name
        """
    )

    current_assignments = db.fetch_checked(
        """
        SELECT
            pm.user_id,
            pm.project_id,
            pm.assigned_at,
            u.username,
            p.project_name,
            p.department_id,
            p.status
        FROM project_managers pm
        JOIN app_users u ON u.user_id = pm.user_id
        JOIN projects p ON p.project_id = pm.project_id
        ORDER BY u.username, p.project_name
        """
    )
except RuntimeError:
    st.error("Unable to load project assignment data.")
    st.stop()

# Current assignments
st.markdown("#### Current assignments")

if current_assignments:
    assignment_rows = [
        {
            "Project Manager": row["username"],
            "Project ID": row["project_id"],
            "Project": row["project_name"],
            "Department ID": row["department_id"],
            "Status": row["status"],
            "Assigned At": str(row["assigned_at"]),
        }
        for row in current_assignments
    ]
    st.dataframe(
        assignment_rows,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No projects have been assigned to Project Managers yet.")

st.markdown("#### Assign a project")

if not project_managers:
    st.info("Create an active Project Manager account first.")
elif not available_projects:
    st.info("No projects are available to assign.")
else:
    manager_options = {
        f"{user['username']} (ID: {user['user_id']})": user["user_id"]
        for user in project_managers
    }
    project_options = {
        (
            f"{project['project_name']} "
            f"(ID: {project['project_id']}, "
            f"Department: {project['department_id']})"
        ): project["project_id"]
        for project in available_projects
    }

    with st.form("admin_assign_project_form"):
        selected_manager_label = st.selectbox(
            "Project Manager",
            options=list(manager_options.keys()),
        )
        selected_project_label = st.selectbox(
            "Project",
            options=list(project_options.keys()),
        )
        assign_project_submitted = st.form_submit_button(
            "Assign project",
            type="primary",
        )

    if assign_project_submitted:
        selected_user_id = manager_options[selected_manager_label]
        selected_project_id = project_options[selected_project_label]

        existing_assignment = db.fetch_checked(
            """
            SELECT 1
            FROM project_managers
            WHERE user_id = %s AND project_id = %s
            """,
            (selected_user_id, selected_project_id),
        )

        if existing_assignment:
            st.warning("This project is already assigned to that user.")
        else:
            inserted = db.execute(
                """
                INSERT INTO project_managers (user_id, project_id)
                VALUES (%s, %s)
                """,
                (selected_user_id, selected_project_id),
            )

            if inserted:
                st.success("Project assigned successfully.")
                st.rerun()
            else:
                st.error("Assignment failed. Check the database connection.")

st.markdown("#### Revoke a project assignment")

if current_assignments:
    revoke_options = {
        (
            f"{row['username']} — {row['project_name']} "
            f"(Project ID: {row['project_id']})"
        ): (row["user_id"], row["project_id"])
        for row in current_assignments
    }

    with st.form("admin_revoke_project_form"):
        selected_assignment_label = st.selectbox(
            "Assignment to revoke",
            options=list(revoke_options.keys()),
        )
        confirm_revoke = st.checkbox(
            "I confirm that this Project Manager should lose access to this project."
        )
        revoke_submitted = st.form_submit_button("Revoke assignment")

    if revoke_submitted:
        if not confirm_revoke:
            st.warning("Confirm the revocation before continuing.")
        else:
            selected_user_id, selected_project_id = revoke_options[
                selected_assignment_label
            ]

            deleted = db.execute(
                """
                DELETE FROM project_managers
                WHERE user_id = %s AND project_id = %s
                """,
                (selected_user_id, selected_project_id),
            )

            if deleted:
                st.success("Project assignment revoked.")
                st.rerun()
            else:
                st.error("The assignment could not be revoked.")
else:
    st.info("There are no assignments to revoke.")
