import streamlit as st

from db.db_manager import DatabaseConnection


# Page Configuration
st.set_page_config(
    page_title="Employee Analytics DW",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Custom CSS
st.markdown(
    """
    <style>
        .stApp { background: #f5f7fb; }
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        .hero {
            background: linear-gradient(135deg, #172554 0%, #2563eb 55%, #38bdf8 100%);
            padding: 2.5rem 3rem; border-radius: 20px; color: white;
            margin-bottom: 2rem; box-shadow: 0 10px 30px rgba(37, 99, 235, 0.20);
        }
        .hero h1 { font-size: 2.6rem; margin-bottom: 0.5rem; font-weight: 700; }
        .hero p { font-size: 1.1rem; opacity: 0.9; margin-bottom: 0; }
        .hero-badge {
            display: inline-block; background: rgba(255,255,255,0.15);
            padding: 0.4rem 0.9rem; border-radius: 20px; font-size: 0.85rem;
            margin-bottom: 1rem; border: 1px solid rgba(255,255,255,0.2);
        }
        .metric-card {
            background: white; padding: 1.5rem; border-radius: 16px;
            border: 1px solid #e5e7eb; box-shadow: 0 5px 15px rgba(0,0,0,0.05);
            transition: transform 0.2s ease, box-shadow 0.2s ease; min-height: 150px;
        }
        .metric-card:hover { transform: translateY(-4px); box-shadow: 0 10px 25px rgba(0,0,0,0.08); }
        .metric-icon { font-size: 1.8rem; margin-bottom: 0.5rem; }
        .metric-label { color: #64748b; font-size: 0.9rem; font-weight: 500; }
        .metric-value { font-size: 2rem; font-weight: 700; color: #0f172a; margin-top: 0.2rem; }
        .metric-change { font-size: 0.8rem; color: #16a34a; margin-top: 0.3rem; }
        .section-title { font-size: 1.35rem; font-weight: 650; color: #0f172a; margin: 1rem 0; }
        .feature-card {
            background: white; padding: 1.5rem; border-radius: 16px;
            border: 1px solid #e5e7eb; min-height: 175px; box-shadow: 0 4px 12px rgba(0,0,0,0.04);
        }
        .feature-icon {
            width: 45px; height: 45px; display: flex; align-items: center;
            justify-content: center; background: #eff6ff; border-radius: 12px;
            font-size: 1.4rem; margin-bottom: 0.8rem;
        }
        .feature-title { font-weight: 650; color: #1e293b; font-size: 1rem; margin-bottom: 0.4rem; }
        .feature-text { color: #64748b; font-size: 0.85rem; line-height: 1.5; }
        .info-banner {
            background: linear-gradient(90deg, #eff6ff, #f0f9ff);
            border: 1px solid #bfdbfe; padding: 1.2rem 1.5rem;
            border-radius: 14px; color: #1e3a8a; margin-top: 1.5rem;
        }
        section[data-testid="stSidebar"] { background: #0f172a; }
        section[data-testid="stSidebar"] * { color: #e2e8f0; }
    </style>
    """,
    unsafe_allow_html=True,
)


# Hero Section
st.markdown(
    """
    <div class="hero">
        <div class="hero-badge">🏢 ENTERPRISE DATA PLATFORM</div>
        <h1>📊 Employee Analytics &amp; Data Warehouse</h1>
        <p>
            Centralized workforce intelligence for employee lifecycle,
            project management, performance tracking, and OLAP analytics.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# Database access
@st.cache_resource
def get_db():
    """Return the shared database connection manager."""
    return DatabaseConnection()


db = get_db()

try:
    employee_rows = db.fetch_checked("SELECT COUNT(*) AS total FROM employees")
    review_rows = db.fetch_checked("SELECT COUNT(*) AS total FROM performance_reviews")
    project_rows = db.fetch_checked("SELECT COUNT(*) AS total FROM projects")
    warehouse_rows = db.fetch_checked(
        """
        SELECT
            (SELECT COUNT(*) FROM employees) +
            (SELECT COUNT(*) FROM employee_history) +
            (SELECT COUNT(*) FROM performance_reviews) +
            (SELECT COUNT(*) FROM projects) +
            (SELECT COUNT(*) FROM employee_projects) +
            (SELECT COUNT(*) FROM departments)
            AS total_records
        """
    )
    performance_rows = db.fetch_checked(
        """
        SELECT ROUND(AVG(performance_score), 2) AS average_score
        FROM fact_performance_reviews
        """
    )
except RuntimeError:
    st.error(
        "Unable to load homepage metrics. Check the database connection "
        "and confirm the required tables are available."
    )
    st.stop()

employee_count = employee_rows[0]["total"] if employee_rows else 0
review_count = review_rows[0]["total"] if review_rows else 0
project_count = project_rows[0]["total"] if project_rows else 0
record_count = warehouse_rows[0]["total_records"] if warehouse_rows else 0
average_score = (
    performance_rows[0]["average_score"]
    if performance_rows and performance_rows[0]["average_score"] is not None
    else "N/A"
)


# KPI Section
st.markdown(
    '<div class="section-title">📈 Platform at a Glance</div>',
    unsafe_allow_html=True,
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-icon">👥</div>
            <div class="metric-label">Total Employees</div>
            <div class="metric-value">{employee_count:,}</div>
            <div class="metric-change">Live database count</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-icon">⭐</div>
            <div class="metric-label">Performance Reviews</div>
            <div class="metric-value">{review_count:,}</div>
            <div class="metric-change">Live database count</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-icon">🚀</div>
            <div class="metric-label">Projects</div>
            <div class="metric-value">{project_count:,}</div>
            <div class="metric-change">Live database count</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col4:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-icon">🗃️</div>
            <div class="metric-label">Records Across Source Tables</div>
            <div class="metric-value">{record_count:,}</div>
            <div class="metric-change">Combined row count</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    f"""
    <div class="info-banner">
        <strong>📊 Average Performance Score:</strong> {average_score}
        <span style="font-size: 0.9rem;">(from the data warehouse fact table)</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)


# Platform Capabilities
st.markdown(
    '<div class="section-title">⚡ Platform Capabilities</div>',
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">👤</div>
            <div class="feature-title">Employee Management</div>
            <div class="feature-text">
                Manage employee onboarding, profiles, departments,
                roles, and organizational information.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">📋</div>
            <div class="feature-title">Performance Analytics</div>
            <div class="feature-text">
                Track performance reviews, ratings, trends,
                and employee development over time.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">🕒</div>
            <div class="feature-title">SCD Type 2 History</div>
            <div class="feature-text">
                Preserve historical employee changes using
                Slowly Changing Dimension Type 2 architecture.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">🎯</div>
            <div class="feature-title">Project Assignment</div>
            <div class="feature-text">
                Monitor employee-project relationships,
                assignments, and workforce allocation.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">🔎</div>
            <div class="feature-title">OLAP Analytics</div>
            <div class="feature-text">
                Explore multidimensional business data with
                interactive analytical views and aggregations.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">🛡️</div>
            <div class="feature-title">Data Warehouse</div>
            <div class="feature-text">
                Centralized analytical storage designed for
                reporting, historical analysis, and BI workloads.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Navigation Banner
st.markdown(
    """
    <div class="info-banner">
        <strong>💡 Getting Started</strong><br>
        Use the navigation menu in the sidebar to explore employee
        management, dashboards, project assignments, performance
        analytics, and data warehouse modules.
    </div>
    """,
    unsafe_allow_html=True,
)


# Footer
st.markdown(
    """
    <div style="
        text-align: center;
        color: #94a3b8;
        font-size: 0.8rem;
        padding: 2rem 0 0.5rem 0;
    ">
        Employee Analytics DW &nbsp;•&nbsp; Enterprise Workforce Intelligence
    </div>
    """,
    unsafe_allow_html=True,
)
