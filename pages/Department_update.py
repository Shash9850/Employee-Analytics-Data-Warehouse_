import streamlit as st
import pandas as pd
from utils.auth import require_permission
from managers.employee_manager import EmployeeManager


st.set_page_config(
    page_title="Department Update",
    page_icon="🔄",
    layout="wide"
)
require_permission("manage_employees")

@st.cache_resource
def get_manager():
    return EmployeeManager()


manager = get_manager()


st.title("🔄 Department Update & SCD Type 2")

st.write(
    "Update an employee's department while preserving "
    "the employee's historical department records."
)

st.divider()


# EMPLOYEE SEARCH

st.subheader("👤 Find Employee")

employee_search = st.text_input(
    "Employee ID",
    placeholder="Enter employee ID"
).strip()


if not employee_search:

    st.info(
        "Enter an Employee ID to continue."
    )

    st.stop()


employees = manager.db.fetch(
    """
    SELECT
        employee_id,
        first_name,
        last_name,
        department_id,
        job_role
    FROM employees
    WHERE employee_id = %s
    """,
    (employee_search,)
)


if not employees:

    st.error(
        f"Employee {employee_search} was not found."
    )

    st.stop()


selected_employee = employees[0]

employee_id = selected_employee["employee_id"]
current_department_id = selected_employee["department_id"]


st.success(
    f"Employee: {selected_employee['first_name']} "
    f"{selected_employee['last_name']} "
    f"({employee_id})"
)

st.write(
    f"**Job Role:** {selected_employee['job_role']}"
)


# LOAD DEPARTMENTS FROM DATABASE

departments = manager.db.fetch(
    """
    SELECT
        department_id,
        department_name
    FROM departments
    ORDER BY department_name
    """
)


if not departments:

    st.error("No departments found.")

    st.stop()


department_options = {
    f"{row['department_id']} - {row['department_name']}":
        row["department_id"]
    for row in departments
}


current_department = manager.db.fetch(
    """
    SELECT department_name
    FROM departments
    WHERE department_id = %s
    """,
    (current_department_id,)
)


if current_department:

    st.info(
        f"Current Department: "
        f"{current_department[0]['department_name']}"
    )


st.divider()


# UPDATE DEPARTMENT

st.subheader("🏢 Change Department")


with st.form("department_update_form"):

    new_department_name = st.selectbox(
        "New Department",
        list(department_options.keys())
    )

    change_date = st.date_input(
        "Effective Change Date"
    )

    submitted = st.form_submit_button(
        "Update Department"
    )


if submitted:

    new_department_id = department_options[
        new_department_name
    ]

    if new_department_id == current_department_id:

        st.warning(
            "The selected department is already "
            "the employee's current department."
        )

    else:

        result = manager.update_department(
            employee_id,
            new_department_id,
            change_date
        )

        if result:

            st.success(
                f"Department updated successfully "
                f"for employee {employee_id}."
            )

            st.rerun()

        else:

            st.error(
                "Unable to update department. "
                "Please check the database error."
            )


st.divider()


# OLAP SCD2 HISTORY

st.subheader("⭐ Employee SCD Type 2 History")


dimension_history = manager.db.fetch(
    """
    SELECT
        employee_sk,
        employee_id,
        first_name,
        last_name,
        department_id,
        effective_start_date,
        effective_end_date,
        is_current
    FROM dim_employee
    WHERE employee_id = %s
    ORDER BY effective_start_date
    """,
    (employee_id,)
)


if dimension_history:

    dimension_df = pd.DataFrame(
        dimension_history
    )

    dimension_df["status"] = dimension_df[
        "is_current"
    ].apply(
        lambda value:
        "Current" if value == 1 else "Historical"
    )

    st.dataframe(
        dimension_df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.warning(
        "No SCD Type 2 dimension records found."
    )