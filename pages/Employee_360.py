import streamlit as st
import pandas as pd
import plotly.express as px

from managers.analytics_manager import AnalyticsManager

from utils.auth import require_permission
# PAGE CONFIGURATION

st.set_page_config(
    page_title="Employee 360°",
    page_icon="👤",
    layout="wide"
)

require_permission("view_employees")
# ANALYTICS MANAGER

manager = AnalyticsManager()


# PAGE HEADER

st.title("👤 Employee 360°")

st.caption(
    "Complete employee profile, performance, project allocation "
    "and SCD Type 2 history"
)


# EMPLOYEE SEARCH

employee_id = st.text_input(
    "Employee ID",
    placeholder="Enter employee ID"
).strip()


if not employee_id:
    st.info("Enter an Employee ID to view the employee profile.")
    st.stop()


# 1. EMPLOYEE PROFILE

employee_data = manager.get_employee_360(employee_id)

if not employee_data:
    st.error("Employee not found.")
    st.stop()

employee = employee_data[0]

# Restrict Department Managers to their assigned department.
auth_user = st.session_state.get("auth_user", {})

if auth_user.get("role") == "Department Manager":
    assigned_department = auth_user.get("department_id")

    if assigned_department is None:
        st.error("Your account has no assigned department.")
        st.stop()

    try:
        department_scope = int(assigned_department)
        employee_department = int(employee["department_id"])
    except (TypeError, ValueError):
        st.error("Unable to verify your department access.")
        st.stop()

    if employee_department != department_scope:
        st.error("You do not have permission to view this employee.")
        st.stop()


st.header(
    f"👤 {employee['first_name']} {employee['last_name']}"
)

st.caption(
    f"Employee ID: {employee['employee_id']}"
)


# Main employee metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Job Role",
        employee["job_role"]
    )

with col2:
   st.metric(
    "Department",
    employee["department_name"]
)

with col3:
    st.metric(
        "Job Level",
        employee["job_level"]
    )

with col4:
    st.metric(
        "Hire Date",
        str(employee["hire_date"])
    )


# Additional information
st.subheader("Employee Information")

info_col1, info_col2, info_col3 = st.columns(3)

with info_col1:
    st.write("**Email**")
    st.write(employee["email"])

    st.write("**Age**")
    st.write(employee["age"])


with info_col2:
    st.write("**Monthly Income**")
    st.write(employee["monthly_income"])

    st.write("**Attrition**")
    st.write(employee["attrition"])


with info_col3:
    st.write("**Employee ID**")
    st.write(employee["employee_id"])

    st.write("**Department ID**")
    st.write(employee["department_id"])


st.divider()


# 2. PERFORMANCE SUMMARY

st.header("📈 Performance Summary")


performance_summary = manager.get_employee_performance_summary(
    employee_id
)


if performance_summary:

    performance = performance_summary[0]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Reviews",
            performance["review_count"]
        )

    with col2:
        st.metric(
            "Average Score",
            performance["average_score"]
        )

    with col3:
        st.metric(
            "Best Score",
            performance["best_score"]
        )

    with col4:
        st.metric(
            "Lowest Score",
            performance["lowest_score"]
        )

else:

    st.info(
        "No performance reviews found for this employee."
    )


# 3. PERFORMANCE TREND

st.subheader("📊 Performance Trend")


performance_trend = manager.get_employee_performance_trend(
    employee_id
)


if performance_trend:

    trend_df = pd.DataFrame(performance_trend)

    fig = px.line(
        trend_df,
        x="year",
        y="average_score",
        markers=True,
        title="Year-wise Average Performance"
    )

    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Average Performance Score",
        hovermode="x unified"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

else:

    st.info(
        "No performance trend data available."
    )


st.divider()


# 4. PROJECT ALLOCATION

st.header("🚀 Project Allocation")


project_data = manager.get_employee_projects(
    employee_id
)


if project_data:

    project_df = pd.DataFrame(project_data)

    # Display project table
    st.dataframe(
        project_df,
        use_container_width=True,
        hide_index=True
    )

    # Allocation chart
    if "allocation_percent" in project_df.columns:

        allocation_df = project_df[
            ["project_name", "allocation_percent"]
        ].copy()

        fig = px.bar(
            allocation_df,
            x="project_name",
            y="allocation_percent",
            title="Project Allocation",
            labels={
                "project_name": "Project",
                "allocation_percent": "Allocation (%)"
            }
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

else:

    st.info(
        "No project assignments found for this employee."
    )


st.divider()


# 5. SCD TYPE 2 DEPARTMENT HISTORY

st.header("🔄 Department History")

st.caption(
    "SCD Type 2 history showing department changes over time."
)


department_history = manager.get_employee_department_history(
    employee_id
)


if department_history:

    history_df = pd.DataFrame(
        department_history
    )

    # Create readable status
    history_df["Status"] = history_df[
        "is_current"
    ].apply(
        lambda value:
        "Current" if value == 1 else "Historical"
    )

    # Display table
    display_df = history_df[
        [
            "department_name",
            "effective_start_date",
            "effective_end_date",
            "Status"
        ]
    ].copy()

    display_df.columns = [
        "Department",
        "Effective Start",
        "Effective End",
        "Status"
    ]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


  
    # SCD2 TIMELINE
  

    st.subheader("Department Timeline")


    timeline_df = history_df[
        [
            "department_name",
            "effective_start_date",
            "effective_end_date",
            "is_current"
        ]
    ].copy()


    # Current records use today's date for visualization
    timeline_df["visual_end_date"] = timeline_df[
        "effective_end_date"
    ]

    timeline_df.loc[
        timeline_df["is_current"] == 1,
        "visual_end_date"
    ] = pd.Timestamp.today().normalize()


    timeline_df["effective_start_date"] = pd.to_datetime(
        timeline_df["effective_start_date"]
    )

    timeline_df["visual_end_date"] = pd.to_datetime(
        timeline_df["visual_end_date"]
    )


    fig = px.timeline(
        timeline_df,
        x_start="effective_start_date",
        x_end="visual_end_date",
        y="department_name",
        color="department_name",
        title="Employee Department History"
    )


    fig.update_yaxes(
        title="Department"
    )

    fig.update_xaxes(
        title="Date"
    )


    st.plotly_chart(
        fig,
        use_container_width=True
    )

else:

    st.info(
        "No department history found for this employee."
    )


st.divider()


# 6. EMPLOYEE STATUS

st.header("📌 Employee Status")


status_col1, status_col2 = st.columns(2)


with status_col1:

    if str(employee["attrition"]).lower() == "yes":
        st.error("Employee has left the organization.")
    else:
        st.success("Employee is currently active.")


with status_col2:

    st.info(
        f"Department ID: {employee['department_id']}"
    )


# FOOTER

st.divider()

st.caption(
    "Employee 360° combines OLTP employee data, performance analytics, "
    "project assignments and SCD Type 2 history."
)