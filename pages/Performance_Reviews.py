import streamlit as st
import pandas as pd
from utils.auth import has_permission, require_permission

from db.db_manager import DatabaseConnection


st.set_page_config(
    page_title="Performance Reviews",
    page_icon="📝",
    layout="wide"
)

require_permission("view_reviews")

@st.cache_resource
def get_db():
    return DatabaseConnection()


db = get_db()


st.title("📝 Performance Reviews")

st.write(
    "Add employee performance reviews and view recent review records."
)

st.divider()


# LOAD EMPLOYEES

employees = db.fetch(
    """
    SELECT
        employee_id,
        first_name,
        last_name,
        job_role
    FROM employees
    ORDER BY employee_id
    """
)


if not employees:
    st.error("No employees found.")
    st.stop()


employee_options = {
    f"{row['employee_id']} - {row['first_name']} {row['last_name']}":
        row["employee_id"]
    for row in employees
}


# REVIEW FORM

if has_permission("create_reviews"):
    st.subheader("➕ Add Performance Review")


    with st.form("performance_review_form"):

        employee_name = st.selectbox(
            "Employee",
            list(employee_options.keys())
        )

        review_date = st.date_input(
            "Review Date"
        )


        review_period = st.selectbox(
        "Review Period",
        [
            "Quarterly",
            "Mid-Year",
            "Annual"
        ]

        )

        col1, col2 = st.columns(2)

        with col1:

            performance_score = st.number_input(
                "Performance Score",
                min_value=0.0,
                max_value=100.0,
                value=75.0,
                step=0.5
            )

            performance_rating = st.slider(
                "Performance Rating",
                min_value=1,
                max_value=5,
                value=3
            )

        with col2:

            manager_rating = st.slider(
                "Manager Rating",
                min_value=1,
                max_value=5,
                value=3
            )

            employee_rating = st.slider(
                "Employee Rating",
                min_value=1,
                max_value=5,
                value=3
            )

        comments = st.text_area(
            "Comments",
            placeholder="Enter review comments..."
        )

        submitted = st.form_submit_button(
            "Submit Review"
        )


    # INSERT REVIEW
    if submitted:
        employee_id = employee_options[employee_name]

        query = """
            CALL sp_add_performance_review(
                %s, %s, %s, %s,
                %s, %s, %s, %s
            )
        """

        params = (
            employee_id,
            review_date,
            review_period,
            performance_score,
            performance_rating,
            manager_rating,
            employee_rating,
            comments
        )

        result = db.execute(query, params)

        if result:
            st.success(
                f"Performance review added successfully "
                f"for employee {employee_id}."
            )
            st.cache_resource.clear()
        else:
            st.error("Unable to add performance review.")

# RECENT REVIEWS

st.subheader("📋 Recent Performance Reviews")


reviews = db.fetch(
    """
    SELECT
        pr.review_id,
        pr.employee_id,
        CONCAT(
            e.first_name,
            ' ',
            e.last_name
        ) AS employee_name,
        pr.review_date,
        pr.review_period,
        pr.performance_score,
        pr.performance_rating,
        pr.manager_rating,
        pr.employee_rating,
        pr.comments
    FROM performance_reviews pr
    JOIN employees e
        ON pr.employee_id = e.employee_id
    ORDER BY pr.review_date DESC, pr.review_id DESC
    LIMIT 200
    """
)


if reviews:

    review_df = pd.DataFrame(reviews)

    st.dataframe(
        review_df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "No performance reviews found."
    )


st.divider()


# REVIEW SUMMARY

st.subheader("📊 Review Summary")


summary = db.fetch(
    """
    SELECT
        performance_rating,
        COUNT(*) AS review_count,
        ROUND(
            AVG(performance_score),
            2
        ) AS average_score
    FROM performance_reviews
    GROUP BY performance_rating
    ORDER BY performance_rating
    """
)


if summary:

    summary_df = pd.DataFrame(summary)

    col1, col2 = st.columns(2)

    with col1:

        st.bar_chart(
            summary_df.set_index(
                "performance_rating"
            )["review_count"]
        )

    with col2:

        st.dataframe(
            summary_df,
            use_container_width=True,
            hide_index=True
        )
