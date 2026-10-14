
"""Employee onboarding page with input validation and duplicate checks."""

import streamlit as st

from managers.employee_manager import EmployeeManager
from models.employee import Employee
from utils.validation import (
    validate_employee_id,
    validate_person_name,
    validate_email,
    validate_employee_metrics,
)


st.set_page_config(
    page_title="Employee Onboarding",
    page_icon="👤",
    layout="wide",
)


@st.cache_resource
def get_manager():
    """Create and reuse the employee manager."""
    return EmployeeManager()


def show_errors(errors):
    """Display each unique validation error once."""
    for error in dict.fromkeys(errors):
        st.error(error)


def main():
    st.title("👤 Employee Onboarding")
    st.caption("Register a new employee after validating the submitted details.")

    manager = get_manager()

    # Load departments from the existing database.
    try:
        departments = manager.get_departments()
    except Exception:
        st.error("Unable to load departments. Please check the database connection.")
        st.stop()

    if not departments:
        st.warning("No departments are available. Add a department before onboarding.")
        st.stop()

    # Support department results represented as dictionaries or tuples.
    department_options = {}

    for department in departments:
        if isinstance(department, dict):
            department_id = department.get("department_id")
            department_name = department.get("department_name")
        else:
            department_id = department[0]
            department_name = department[1]

        if department_id is not None and department_name:
            department_options[str(department_name)] = department_id

    if not department_options:
        st.error("Departments could not be interpreted from the database results.")
        st.stop()

    with st.form("employee_onboarding_form", clear_on_submit=False):
        st.subheader("Basic Information")

        col1, col2 = st.columns(2)

        with col1:
            employee_id = st.text_input(
                "Employee ID *",
                max_chars=20,
                help="Letters, numbers, hyphens and underscores are allowed.",
            )
            first_name = st.text_input("First Name *", max_chars=100)
            last_name = st.text_input("Last Name *", max_chars=100)
            email = st.text_input("Email *", max_chars=150)

        with col2:
            gender = st.selectbox(
                "Gender",
                ["Male", "Female", "Other"],
            )
            department_name = st.selectbox(
                "Department *",
                list(department_options.keys()),
            )
            job_role = st.text_input("Job Role *", max_chars=100)
            education_field = st.text_input(
                "Education Field *",
                max_chars=100,
            )

        st.divider()
        st.subheader("Employment Information")

        col1, col2, col3 = st.columns(3)

        with col1:
            age = st.number_input("Age", 18, 70, 25)
            job_level = st.number_input("Job Level", 1, 5, 1)
            monthly_income = st.number_input(
                "Monthly Income",
                min_value=0,
                max_value=100000,
                value=0,
            )
            daily_rate = st.number_input(
                "Daily Rate",
                min_value=0,
                max_value=10000,
                value=0,
            )
            hourly_rate = st.number_input(
                "Hourly Rate",
                min_value=0,
                max_value=1000,
                value=0,
            )
            distance_from_home = st.number_input(
                "Distance From Home",
                min_value=0,
                max_value=100,
                value=0,
            )

        with col2:
            business_travel = st.selectbox(
                "Business Travel",
                [
                    "Non-Travel",
                    "Travel_Rarely",
                    "Travel_Frequently",
                ],
            )
            job_involvement = st.number_input(
                "Job Involvement (1–4)", 1, 4, 3
            )
            job_satisfaction = st.number_input(
                "Job Satisfaction (1–4)", 1, 4, 3
            )
            environment_satisfaction = st.number_input(
                "Environment Satisfaction (1–4)", 1, 4, 3
            )
            relationship_satisfaction = st.number_input(
                "Relationship Satisfaction (1–4)", 1, 4, 3
            )
            performance_rating = st.number_input(
                "Performance Rating (1–5)", 1, 5, 3
            )
            percent_salary_hike = st.number_input(
                "Percent Salary Hike",
                min_value=0,
                max_value=100,
                value=0,
            )

        with col3:
            overtime = st.selectbox("Overtime", ["No", "Yes"])
            marital_status = st.selectbox(
                "Marital Status",
                ["Single", "Married", "Divorced"],
            )
            stock_option_level = st.number_input(
                "Stock Option Level", 0, 3, 0
            )
            total_working_years = st.number_input(
                "Total Working Years", 0, 50, 0
            )
            years_at_company = st.number_input(
                "Years at Company", 0, 50, 0
            )
            years_in_current_role = st.number_input(
                "Years in Current Role", 0, 50, 0
            )
            years_since_last_promotion = st.number_input(
                "Years Since Last Promotion", 0, 50, 0
            )
            years_with_current_manager = st.number_input(
                "Years with Current Manager", 0, 50, 0
            )

        col1, col2 = st.columns(2)

        with col1:
            training_times_last_year = st.number_input(
                "Training Times Last Year", 0, 20, 0
            )
            work_life_balance = st.number_input(
                "Work-Life Balance (1–4)", 1, 4, 3
            )

        with col2:
            num_companies_worked = st.number_input(
                "Number of Companies Worked", 0, 20, 0
            )
            attrition = st.selectbox("Attrition", ["No", "Yes"])

        hire_date = st.date_input(
            "Hire Date",
            help="A future hire date is not allowed by the current validation rules.",
        )

        submitted = st.form_submit_button(
            "Register Employee",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    # Normalize text before validating and querying the database.
    employee_id = employee_id.strip()
    first_name = first_name.strip()
    last_name = last_name.strip()
    email = email.strip()
    job_role = job_role.strip()
    education_field = education_field.strip()

    errors = []

    # Required fields are checked only once.
    required_fields = {
        "Employee ID": employee_id,
        "First name": first_name,
        "Last name": last_name,
        "Email": email,
        "Job role": job_role,
        "Education field": education_field,
    }

    for label, value in required_fields.items():
        if not value:
            errors.append(f"{label} is required.")

    # Run format checks only when the relevant value is present.
    if employee_id:
        error = validate_employee_id(employee_id)
        if error:
            errors.append(error)

    if first_name:
        error = validate_person_name(first_name, "First name")
        if error:
            errors.append(error)

    if last_name:
        error = validate_person_name(last_name, "Last name")
        if error:
            errors.append(error)

    if email:
        error = validate_email(email)
        if error:
            errors.append(error)

    # Validate relationships between employment metrics.
    metrics = {
        "total_working_years": total_working_years,
        "years_at_company": years_at_company,
        "years_in_current_role": years_in_current_role,
        "years_since_last_promotion": years_since_last_promotion,
        "years_with_current_manager": years_with_current_manager,
        "hire_date": hire_date,
    }
    errors.extend(validate_employee_metrics(metrics))

    if errors:
        show_errors(errors)
        st.warning("Please correct the validation errors before submitting.")
        return

    # Check duplicates using a method that raises on database query failures.
    # This prevents a failed lookup from being treated as a clean result.
    try:
        duplicate_rows = manager.db.fetch_checked(
            """
            SELECT employee_id, email
            FROM employees
            WHERE LOWER(TRIM(employee_id)) = LOWER(TRIM(%s))
               OR LOWER(TRIM(email)) = LOWER(TRIM(%s))
            """,
            (employee_id, email),
        )
    except Exception:
        st.error(
            "Unable to verify whether this Employee ID or email already exists. "
            "No employee was submitted. Please check the database and try again."
        )
        return

    duplicate_ids = {
        str(row["employee_id"]).strip().casefold()
        for row in duplicate_rows
        if row.get("employee_id") is not None
    }
    duplicate_emails = {
        str(row["email"]).strip().casefold()
        for row in duplicate_rows
        if row.get("email") is not None
    }

    duplicate_found = False

    if employee_id.casefold() in duplicate_ids:
        st.error("This Employee ID already exists.")
        duplicate_found = True

    if email.casefold() in duplicate_emails:
        st.error("This email address is already registered.")
        duplicate_found = True

    if duplicate_found:
        st.warning("No employee was submitted. Please correct the duplicate details.")
        return

    # Construct the existing Employee model and use the existing manager/SP.
    try:
        employee = Employee(
            employee_id=employee_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            gender=gender,
            age=age,
            department_id=department_options[department_name],
            job_role=job_role,
            education_field=education_field,
            job_level=job_level,
            monthly_income=monthly_income,
            daily_rate=daily_rate,
            hourly_rate=hourly_rate,
            business_travel=business_travel,
            distance_from_home=distance_from_home,
            job_involvement=job_involvement,
            job_satisfaction=job_satisfaction,
            environment_satisfaction=environment_satisfaction,
            relationship_satisfaction=relationship_satisfaction,
            performance_rating=performance_rating,
            percent_salary_hike=percent_salary_hike,
            overtime=overtime,
            marital_status=marital_status,
            stock_option_level=stock_option_level,
            total_working_years=total_working_years,
            years_at_company=years_at_company,
            years_in_current_role=years_in_current_role,
            years_since_last_promotion=years_since_last_promotion,
            years_with_current_manager=years_with_current_manager,
            training_times_last_year=training_times_last_year,
            work_life_balance=work_life_balance,
            num_companies_worked=num_companies_worked,
            attrition=attrition,
            hire_date=hire_date,
        )

        result = manager.add_employee(employee)

        if result:
            st.success(
                f"Employee {employee_id} ({first_name} {last_name}) "
                "was registered successfully."
            )
            st.info("You can now open the employee list or analytics dashboard.")
        else:
            st.error(
                "The employee could not be registered. "
                "Check the application logs and database constraints."
            )

    except Exception:
        st.error(
            "An unexpected error occurred while registering the employee. "
            "Please check the application logs."
        )


if __name__ == "__main__":
    main()
