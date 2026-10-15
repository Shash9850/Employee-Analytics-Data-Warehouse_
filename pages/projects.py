
import streamlit as st
import pandas as pd
from datetime import date

from models.project import Project
from managers.project_manager import ProjectManager
from utils.auth import has_permission, require_permission


st.set_page_config(
    page_title="Project Management",
    page_icon="📁",
    layout="wide",
)

require_permission("view_projects")


@st.cache_resource
def get_manager():
    """Return the shared project manager."""
    return ProjectManager()


manager = get_manager()
db = manager.db

auth_user = st.session_state.get("auth_user", {})
user_role = auth_user.get("role")
user_id = auth_user.get("user_id")

is_admin = user_role == "Admin"
is_project_manager = user_role == "Project Manager"
is_department_manager = user_role == "Department Manager"
is_executive = user_role == "Executive"

can_assign = is_admin or (
    is_project_manager and has_permission("manage_projects")
)

st.title("📁 Project Management")

if is_admin:
    st.caption("Administrator access: all projects and allocations.")
elif is_project_manager:
    st.caption("Project Manager access: only projects assigned to you.")
elif is_department_manager:
    st.caption("Department Manager access: projects in your department.")
elif is_executive:
    st.caption("Executive access: read-only project reporting.")

st.divider()


# ---------------------------------------------------------
# VALIDATE USER SCOPE
# ---------------------------------------------------------

department_scope = None

if is_department_manager:
    assigned_department = auth_user.get("department_id")

    if assigned_department is None:
        st.error(
            "Your account has no department assigned. "
            "Contact an administrator."
        )
        st.stop()

    try:
        department_scope = int(assigned_department)
    except (TypeError, ValueError):
        st.error("Your department assignment is invalid.")
        st.stop()

if is_project_manager and user_id is None:
    st.error("Your account session is missing its user ID. Please log in again.")
    st.stop()


# ---------------------------------------------------------
# LOAD PROJECTS WITH ROLE-BASED SCOPE
# ---------------------------------------------------------

if is_admin or is_executive:
    projects = db.fetch(
        """
        SELECT
            p.project_id,
            p.project_name,
            p.department_id,
            d.department_name,
            p.start_date,
            p.end_date,
            p.budget,
            p.status
        FROM projects p
        LEFT JOIN departments d
            ON p.department_id = d.department_id
        ORDER BY p.project_id
        """
    )

elif is_project_manager:
    projects = db.fetch(
        """
        SELECT
            p.project_id,
            p.project_name,
            p.department_id,
            d.department_name,
            p.start_date,
            p.end_date,
            p.budget,
            p.status
        FROM projects p
        JOIN project_managers pm
            ON pm.project_id = p.project_id
        LEFT JOIN departments d
            ON p.department_id = d.department_id
        WHERE pm.user_id = %s
        ORDER BY p.project_id
        """,
        (user_id,),
    )

elif is_department_manager:
    projects = db.fetch(
        """
        SELECT
            p.project_id,
            p.project_name,
            p.department_id,
            d.department_name,
            p.start_date,
            p.end_date,
            p.budget,
            p.status
        FROM projects p
        LEFT JOIN departments d
            ON p.department_id = d.department_id
        WHERE p.department_id = %s
        ORDER BY p.project_id
        """,
        (department_scope,),
    )

else:
    st.error("Your role is not authorized to view projects.")
    st.stop()


# ---------------------------------------------------------
# SUCCESS MESSAGES
# ---------------------------------------------------------

for message_key in (
    "project_success_message",
    "assignment_success_message",
):
    if message_key in st.session_state:
        st.success(st.session_state.pop(message_key))


# ---------------------------------------------------------
# PROJECT OVERVIEW
# ---------------------------------------------------------

st.subheader("📌 Project Overview")

if projects:
    project_df = pd.DataFrame(projects)
    st.dataframe(
        project_df,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info(
        "No projects are available in your access scope."
        if is_project_manager
        else "No projects found."
    )


# ---------------------------------------------------------
# CREATE PROJECT — ADMIN ONLY
# ---------------------------------------------------------

if is_admin:
    st.divider()
    st.subheader("➕ Create New Project")

    departments = db.fetch(
        """
        SELECT department_id, department_name
        FROM departments
        ORDER BY department_name
        """
    )

    if not departments:
        st.warning("No departments are available.")
    else:
        department_options = {
            row["department_name"]: row["department_id"]
            for row in departments
        }

        with st.form("create_project_form"):
            col1, col2 = st.columns(2)

            with col1:
                project_id = st.number_input(
                    "Project ID",
                    min_value=1,
                    step=1,
                )
                project_name = st.text_input(
                    "Project Name",
                    placeholder="Enter project name",
                )
                selected_department = st.selectbox(
                    "Department",
                    list(department_options.keys()),
                )
                project_start_date = st.date_input(
                    "Project Start Date",
                    value=date.today(),
                )

            with col2:
                project_end_date = st.date_input(
                    "Project End Date",
                    value=date.today(),
                )
                budget = st.number_input(
                    "Budget",
                    min_value=0.0,
                    step=1000.0,
                    value=0.0,
                    format="%.2f",
                )
                status = st.selectbox(
                    "Project Status",
                    ["Planned", "Active", "Completed", "On Hold"],
                )

            create_submitted = st.form_submit_button(
                "Create Project",
                type="primary",
            )

        if create_submitted:
            # Recheck role at the point of action.
            if st.session_state.get("auth_user", {}).get("role") != "Admin":
                st.error("Only administrators can create projects.")
                st.stop()

            if not project_name.strip():
                st.error("Project name is required.")

            elif project_end_date < project_start_date:
                st.error(
                    "Project end date cannot be before its start date."
                )

            else:
                existing_project = db.fetch(
                    """
                    SELECT project_id
                    FROM projects
                    WHERE project_id = %s
                    """,
                    (int(project_id),),
                )

                if existing_project:
                    st.error(
                        f"Project ID {int(project_id)} already exists."
                    )
                else:
                    project = Project(
                        project_id=int(project_id),
                        project_name=project_name.strip(),
                        department_id=department_options[
                            selected_department
                        ],
                        start_date=project_start_date,
                        end_date=project_end_date,
                        budget=budget,
                        status=status,
                    )

                    if manager.add_project(project):
                        st.session_state["project_success_message"] = (
                            f"Project '{project_name.strip()}' created successfully."
                        )
                        st.rerun()
                    else:
                        st.error(
                            "Unable to create the project. "
                            "Check the application/database logs."
                        )


# ---------------------------------------------------------
# ASSIGN EMPLOYEE — ADMIN OR PROJECT MANAGER
# ---------------------------------------------------------

if can_assign:
    st.divider()
    st.subheader("➕ Assign Employee to Project")

    if not projects:
        st.info(
            "No projects are assigned to your account. "
            "Ask an administrator to assign projects to you."
            if is_project_manager
            else "Create a project before assigning employees."
        )
    else:
        # Admins and Project Managers can staff projects.
        # Department Managers do not get this form.
        employees = db.fetch(
            """
            SELECT
                employee_id,
                first_name,
                last_name,
                department_id,
                job_role
            FROM employees
            ORDER BY employee_id
            """
        )

        if not employees:
            st.warning("No employees were found.")
        else:
            employee_options = {
                (
                    f"{row['employee_id']} - "
                    f"{row['first_name']} {row['last_name']}"
                ): row["employee_id"]
                for row in employees
            }

            project_options = {
                f"{row['project_id']} - {row['project_name']}":
                    row["project_id"]
                for row in projects
            }

            with st.form("project_assignment_form"):
                employee_label = st.selectbox(
                    "Employee",
                    list(employee_options.keys()),
                )
                project_label = st.selectbox(
                    "Project",
                    list(project_options.keys()),
                )
                allocation_percent = st.slider(
                    "Allocation Percentage",
                    min_value=10,
                    max_value=100,
                    value=100,
                    step=10,
                )

                col1, col2 = st.columns(2)

                with col1:
                    assignment_start_date = st.date_input(
                        "Assignment Start Date",
                        value=date.today(),
                    )

                with col2:
                    assignment_end_date = st.date_input(
                        "Assignment End Date",
                        value=date.today(),
                    )

                assign_submitted = st.form_submit_button(
                    "Assign Employee",
                    type="primary",
                )

            if assign_submitted:
                current_user = st.session_state.get("auth_user", {})
                current_role = current_user.get("role")
                current_user_id = current_user.get("user_id")

                # Validate permissions again when the form is submitted.
                if current_role not in ("Admin", "Project Manager"):
                    st.error(
                        "You are not authorized to assign employees."
                    )
                    st.stop()

                employee_id = employee_options[employee_label]
                selected_project_id = project_options[project_label]

                # Verify that the selected project is still in scope.
                if current_role == "Admin":
                    authorized_project = db.fetch(
                        """
                        SELECT project_id
                        FROM projects
                        WHERE project_id = %s
                        """,
                        (selected_project_id,),
                    )
                else:
                    authorized_project = db.fetch(
                        """
                        SELECT p.project_id
                        FROM projects p
                        JOIN project_managers pm
                            ON pm.project_id = p.project_id
                        WHERE p.project_id = %s
                          AND pm.user_id = %s
                        """,
                        (selected_project_id, current_user_id),
                    )

                if not authorized_project:
                    st.error(
                        "You cannot assign employees to that project. "
                        "Your project access may have changed."
                    )
                    st.stop()

                if assignment_end_date < assignment_start_date:
                    st.error(
                        "Assignment end date cannot be before "
                        "the start date."
                    )
                else:
                    success = manager.assign_employee(
                        employee_id=employee_id,
                        project_id=selected_project_id,
                        allocation_percent=allocation_percent,
                        start_date=assignment_start_date,
                        end_date=assignment_end_date,
                    )

                    if success:
                        st.session_state["assignment_success_message"] = (
                            f"Employee {employee_id} assigned to "
                            f"project {selected_project_id}."
                        )
                        st.rerun()
                    else:
                        st.error(
                            "Unable to assign the employee. "
                            "Check the application/database logs."
                        )


# ---------------------------------------------------------
# PROJECT ALLOCATION SUMMARY — SCOPED REPORTING
# ---------------------------------------------------------

st.divider()
st.subheader("📊 Project Allocation Summary")

st.write(
    "View employee counts and total allocation for projects "
    "within your authorized scope."
)

if is_project_manager:
    summary = db.fetch(
        """
        SELECT
            p.project_id,
            p.project_name,
            COUNT(ep.assignment_id) AS employee_count,
            COALESCE(SUM(ep.allocation_percent), 0) AS total_allocation
        FROM projects p
        JOIN project_managers pm
            ON pm.project_id = p.project_id
        LEFT JOIN employee_projects ep
            ON ep.project_id = p.project_id
        WHERE pm.user_id = %s
        GROUP BY p.project_id, p.project_name
        ORDER BY employee_count DESC
        LIMIT 20
        """,
        (user_id,),
    )

elif is_department_manager:
    summary = db.fetch(
        """
        SELECT
            p.project_id,
            p.project_name,
            COUNT(ep.assignment_id) AS employee_count,
            COALESCE(SUM(ep.allocation_percent), 0) AS total_allocation
        FROM projects p
        LEFT JOIN employee_projects ep
            ON ep.project_id = p.project_id
        WHERE p.department_id = %s
        GROUP BY p.project_id, p.project_name
        ORDER BY employee_count DESC
        LIMIT 20
        """,
        (department_scope,),
    )

else:
    # Admin and Executive see organization-wide summaries.
    summary = db.fetch(
        """
        SELECT
            p.project_id,
            p.project_name,
            COUNT(ep.assignment_id) AS employee_count,
            COALESCE(SUM(ep.allocation_percent), 0) AS total_allocation
        FROM projects p
        LEFT JOIN employee_projects ep
            ON ep.project_id = p.project_id
        GROUP BY p.project_id, p.project_name
        ORDER BY employee_count DESC
        LIMIT 20
        """
    )

if summary:
    summary_df = pd.DataFrame(summary)

    col1, col2 = st.columns([2, 1], gap="large")

    with col1:
        st.bar_chart(
            summary_df.set_index("project_name")["employee_count"]
        )

    with col2:
        st.dataframe(
            summary_df,
            use_container_width=True,
            hide_index=True,
        )
else:
    st.info("No allocation summary is available for your scope.")


# ---------------------------------------------------------
# EMPLOYEE-LEVEL ASSIGNMENT DETAILS
# Executive reporting remains aggregate-only.
# ---------------------------------------------------------

if not is_executive:
    st.divider()
    st.subheader("📋 Project Assignments")

    if is_project_manager:
        assignments = db.fetch(
            """
            SELECT
                ep.assignment_id,
                ep.employee_id,
                CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
                ep.project_id,
                p.project_name,
                ep.allocation_percent,
                ep.start_date,
                ep.end_date
            FROM employee_projects ep
            JOIN employees e
                ON ep.employee_id = e.employee_id
            JOIN projects p
                ON ep.project_id = p.project_id
            JOIN project_managers pm
                ON pm.project_id = p.project_id
            WHERE pm.user_id = %s
            ORDER BY ep.assignment_id DESC
            LIMIT 200
            """,
            (user_id,),
        )

    elif is_department_manager:
        # Do not reveal employees from other departments.
        assignments = db.fetch(
            """
            SELECT
                ep.assignment_id,
                ep.employee_id,
                CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
                ep.project_id,
                p.project_name,
                ep.allocation_percent,
                ep.start_date,
                ep.end_date
            FROM employee_projects ep
            JOIN employees e
                ON ep.employee_id = e.employee_id
            JOIN projects p
                ON ep.project_id = p.project_id
            WHERE p.department_id = %s
              AND e.department_id = %s
            ORDER BY ep.assignment_id DESC
            LIMIT 200
            """,
            (department_scope, department_scope),
        )

    else:
        # Admin can see all employee-level assignments.
        assignments = db.fetch(
            """
            SELECT
                ep.assignment_id,
                ep.employee_id,
                CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
                ep.project_id,
                p.project_name,
                ep.allocation_percent,
                ep.start_date,
                ep.end_date
            FROM employee_projects ep
            JOIN employees e
                ON ep.employee_id = e.employee_id
            JOIN projects p
                ON ep.project_id = p.project_id
            ORDER BY ep.assignment_id DESC
            LIMIT 200
            """
        )

    if assignments:
        st.dataframe(
            pd.DataFrame(assignments),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No employee assignments found in your access scope.")
else:
    st.info(
        "Employee-level assignment details are hidden for the Executive role."
    )
