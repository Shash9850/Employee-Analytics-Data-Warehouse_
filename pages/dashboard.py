import streamlit as st
import pandas as pd
import plotly.express as px

from db.db_manager import DatabaseConnection
from managers.analytics_manager import AnalyticsManager
from utils.auth import require_permission



# PAGE CONFIG


st.set_page_config(
    page_title="Employee Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)


require_permission("view_department_analytics")


# CUSTOM CSS


st.markdown(
    """
    <style>

    /* Page */
    .stApp {
        background: #f6f8fc;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1450px;
    }

    /* Main title */
    .main-title {
        font-size: 2.2rem;
        font-weight: 750;
        color: #172033;
        margin-bottom: 0.2rem;
    }

    .main-subtitle {
        color: #667085;
        font-size: 0.95rem;
        margin-bottom: 1.8rem;
    }

    /* Section headings */
    .section-title {
        font-size: 1.35rem;
        font-weight: 700;
        color: #172033;
        margin-top: 2rem;
        margin-bottom: 0.25rem;
    }

    .section-description {
        color: #667085;
        font-size: 0.88rem;
        margin-bottom: 1rem;
    }

    /* KPI cards */
    .kpi-card {
        background: #ffffff;
        border: 1px solid #e8ebf2;
        border-radius: 16px;
        padding: 1.25rem 1.4rem;
        min-height: 125px;
        box-shadow: 0 4px 16px rgba(16, 24, 40, 0.05);
    }

    .kpi-icon {
        font-size: 1.55rem;
        margin-bottom: 0.5rem;
    }

    .kpi-label {
        color: #667085;
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    .kpi-value {
        color: #101828;
        font-size: 1.75rem;
        font-weight: 750;
        margin-top: 0.2rem;
    }

    /* Content cards */
    .content-card {
        background: #ffffff;
        border: 1px solid #e8ebf2;
        border-radius: 16px;
        padding: 1rem;
        box-shadow: 0 4px 16px rgba(16, 24, 40, 0.04);
    }

    /* Dataframes */
    div[data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #e8ebf2;
    }

    /* Metrics fallback */
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e8ebf2;
        border-radius: 16px;
        padding: 1rem;
        box-shadow: 0 4px 16px rgba(16, 24, 40, 0.04);
    }

    </style>
    """,
    unsafe_allow_html=True
)



# DATABASE


@st.cache_resource
def get_db():
    return DatabaseConnection()


@st.cache_resource
def get_analytics_manager():
    return AnalyticsManager()


db = get_db()
analytics_manager = get_analytics_manager()



# HEADER


st.markdown(
    """
    <div class="main-title">
        📊 Employee Analytics Dashboard
    </div>

    <div class="main-subtitle">
        Monitor employee performance, departments, projects, and attrition.
    </div>
    """,
    unsafe_allow_html=True
)



# KPI CARDS



# KPI CARDS — live database metrics

try:
    employees = db.fetch_checked("""
        SELECT COUNT(*) AS total
        FROM employees
    """)

    reviews = db.fetch_checked("""
        SELECT COUNT(*) AS total
        FROM performance_reviews
    """)

    projects = db.fetch_checked("""
        SELECT COUNT(*) AS total
        FROM projects
    """)

    performance = db.fetch_checked("""
        SELECT ROUND(AVG(performance_score), 2) AS average_score
        FROM fact_performance_reviews
    """)

except RuntimeError:
    st.error(
        "Unable to load dashboard KPIs. "
        "Check the database connection and required tables."
    )
    st.stop()

employee_count = employees[0]["total"] if employees else 0
review_count = reviews[0]["total"] if reviews else 0
project_count = projects[0]["total"] if projects else 0

average_score = (
    performance[0]["average_score"]
    if performance and performance[0]["average_score"] is not None
    else "N/A"
)



col1, col2, col3, col4 = st.columns(
    4,
    gap="medium"
)


with col1:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-icon">👥</div>
            <div class="kpi-label">Total Employees</div>
            <div class="kpi-value">
                {employee_count:,}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with col2:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-icon">📝</div>
            <div class="kpi-label">Performance Reviews</div>
            <div class="kpi-value">
                {review_count:,}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with col3:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-icon">📁</div>
            <div class="kpi-label">Projects</div>
            <div class="kpi-value">
                {project_count:,}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with col4:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-icon">⭐</div>
            <div class="kpi-label">Average Performance</div>
            <div class="kpi-value">
                {average_score}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


st.divider()



# YEAR-OVER-YEAR PERFORMANCE


st.markdown(
    '<div class="section-title">'
    '📈 Year-over-Year Performance'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-description">'
    'Average performance score by year'
    '</div>',
    unsafe_allow_html=True
)


yearly = analytics_manager.get_year_over_year_performance()

if yearly:

    yearly_df = pd.DataFrame(yearly)

    yearly_df["year"] = yearly_df["year_number"].astype(str)

    chart_col, table_col = st.columns(
        [2, 1],
        gap="large"
    )

    with chart_col:

        st.markdown(
            '<div class="content-card">',
            unsafe_allow_html=True
        )

        fig = px.line(
            yearly_df,
            x="year",
            y="average_score",
            markers=True,
            title="Year-over-Year Performance"
        )

        fig.update_layout(
            xaxis_title="Year",
            yaxis_title="Average Performance Score",
            hovermode="x unified",
            margin=dict(
                l=20,
                r=20,
                t=60,
                b=20
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )

    with table_col:

        st.dataframe(
            yearly_df[
                [
                    "year_number",
                    "average_score",
                    "previous_year_score",
                    "score_change"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

else:

    st.info(
        "No yearly performance data available."
    )



# DEPARTMENT PERFORMANCE


st.markdown(
    '<div class="section-title">'
    '🏢 Department Performance'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-description">'
    'Compare average performance across departments'
    '</div>',
    unsafe_allow_html=True
)


departments = (
    analytics_manager
    .get_department_performance()
)


if departments:

    department_df = pd.DataFrame(
        departments
    )

    chart_col, table_col = st.columns(
        [2, 1],
        gap="large"
    )

    with chart_col:

        st.markdown(
            '<div class="content-card">',
            unsafe_allow_html=True
        )

        fig = px.bar(
            department_df,
            x="department_name",
            y="average_score",
            text_auto=".2f",
            title="Average Performance by Department"
        )

        fig.update_layout(
            xaxis_title="Department",
            yaxis_title="Average Performance Score",
            margin=dict(
                l=20,
                r=20,
                t=60,
                b=20
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )

    with table_col:

        st.dataframe(
            department_df,
            use_container_width=True,
            hide_index=True
        )

else:

    st.info(
        "No department performance data available."
    )



# TOP-PERFORMING EMPLOYEES


st.markdown(
    '<div class="section-title">'
    '🏆 Top-Performing Employees'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-description">'
    'Employee ranking generated using the warehouse analytics '
    'and SQL window functions.'
    '</div>',
    unsafe_allow_html=True
)


rankings = (
    analytics_manager
    .get_employee_rankings()
)


if rankings:

    ranking_df = pd.DataFrame(
        rankings
    )

    # Display the complete ranking table.
    st.dataframe(
        ranking_df,
        use_container_width=True,
        hide_index=True
    )

    # Plot top 20 for readability.
    top_ranking_df = ranking_df.head(20).copy()

    # Build a readable employee label if available.
    if "employee_name" in top_ranking_df.columns:

        employee_label = "employee_name"

    elif (
        "first_name" in top_ranking_df.columns
        and "last_name" in top_ranking_df.columns
    ):

        top_ranking_df["employee_name"] = (
            top_ranking_df["first_name"]
            + " "
            + top_ranking_df["last_name"]
        )

        employee_label = "employee_name"

    else:

        employee_label = (
            "employee_id"
            if "employee_id" in top_ranking_df.columns
            else top_ranking_df.columns[0]
        )

    # Determine the performance column used by the manager.
    if "average_score" in top_ranking_df.columns:

        performance_column = "average_score"

    elif "average_performance" in top_ranking_df.columns:

        performance_column = "average_performance"

    else:

        performance_column = None

    if performance_column:

        fig = px.bar(
            top_ranking_df,
            x=employee_label,
            y=performance_column,
            title="Top 20 Employee Performance",
            text_auto=".2f"
        )

        fig.update_layout(
            xaxis_title="Employee",
            yaxis_title="Average Performance Score",
            xaxis_tickangle=-45,
            margin=dict(
                l=20,
                r=20,
                t=60,
                b=100
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

else:

    st.info(
        "No employee ranking data available."
    )



# PROJECT WORKLOAD


st.markdown(
    '<div class="section-title">'
    '📁 Project Workload'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-description">'
    'Number of employees assigned to each project'
    '</div>',
    unsafe_allow_html=True
)


workload = (
    analytics_manager
    .get_project_workload()
)


if workload:

    workload_df = pd.DataFrame(
        workload
    )

    chart_col, table_col = st.columns(
        [2, 1],
        gap="large"
    )

    with chart_col:

        st.markdown(
            '<div class="content-card">',
            unsafe_allow_html=True
        )

        chart_df = (
            workload_df
            .head(15)
            .copy()
        )

        fig = px.bar(
            chart_df,
            x="project_name",
            y="employee_count",
            title="Employees Assigned by Project",
            text_auto=True
        )

        fig.update_layout(
            xaxis_title="Project",
            yaxis_title="Assigned Employees",
            xaxis_tickangle=-45,
            margin=dict(
                l=20,
                r=20,
                t=60,
                b=100
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )

    with table_col:

        st.dataframe(
            workload_df,
            use_container_width=True,
            hide_index=True
        )

else:

    st.info(
        "No project workload data available."
    )



# ATTRITION ANALYSIS


st.markdown(
    '<div class="section-title">'
    '⚠️ Attrition Analysis'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-description">'
    'Employee attrition distribution'
    '</div>',
    unsafe_allow_html=True
)


attrition = db.fetch(
    """
    SELECT
        attrition,
        COUNT(*) AS employee_count
    FROM employees
    GROUP BY attrition
    ORDER BY employee_count DESC
    """
)


if attrition:

    attrition_df = pd.DataFrame(
        attrition
    )

    chart_col, table_col = st.columns(
        [2, 1],
        gap="large"
    )

    with chart_col:

        st.markdown(
            '<div class="content-card">',
            unsafe_allow_html=True
        )

        fig = px.bar(
            attrition_df,
            x="attrition",
            y="employee_count",
            text_auto=True,
            title="Employee Attrition Distribution"
        )

        fig.update_layout(
            xaxis_title="Attrition",
            yaxis_title="Employees",
            margin=dict(
                l=20,
                r=20,
                t=60,
                b=20
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )

    with table_col:

        st.dataframe(
            attrition_df,
            use_container_width=True,
            hide_index=True
        )

else:

    st.info(
        "No attrition data available."
    )