
"""Reusable input validation helpers for the employee analytics app."""

import re
from datetime import date


def validate_required_fields(fields):
    """Return errors for required fields that are blank."""
    errors = []

    for label, value in fields.items():
        if value is None or not str(value).strip():
            errors.append(f"{label} is required.")

    return errors


def validate_employee_id(employee_id):
    """Allow letters, digits, hyphens, and underscores in employee IDs."""
    employee_id = employee_id.strip()

    if not employee_id:
        return "Employee ID is required."

    if len(employee_id) > 20:
        return "Employee ID must be 20 characters or fewer."

    if not re.fullmatch(r"[A-Za-z0-9_-]+", employee_id):
        return (
            "Employee ID may contain only letters, numbers, "
            "hyphens, and underscores."
        )

    return None


def validate_person_name(value, label):
    """Validate a person's name without accepting blank input."""
    value = value.strip()

    if not value:
        return f"{label} is required."

    if len(value) > 100:
        return f"{label} must be 100 characters or fewer."

    if not re.fullmatch(r"[^\W\d_][\w .'-]*", value, flags=re.UNICODE):
        return f"{label} contains unsupported characters."

    return None


def validate_email(email):
    """Perform basic email-format and database-length validation."""
    email = email.strip()

    if not email:
        return "Email is required."

    if len(email) > 150:
        return "Email must be 150 characters or fewer."

    pattern = r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$"

    if not re.fullmatch(pattern, email):
        return "Enter a valid email address."

    return None


def validate_employee_metrics(data):
    """Validate related employee metrics and their logical consistency."""
    errors = []

    if data["years_in_current_role"] > data["years_at_company"]:
        errors.append(
            "Years in current role cannot exceed years at the company."
        )

    if data["years_since_last_promotion"] > data["years_at_company"]:
        errors.append(
            "Years since last promotion cannot exceed years at the company."
        )

    if data["years_with_current_manager"] > data["years_at_company"]:
        errors.append(
            "Years with current manager cannot exceed years at the company."
        )

    if data["years_at_company"] > data["total_working_years"]:
        errors.append(
            "Years at the company cannot exceed total working years."
        )

    if data["hire_date"] > date.today():
        errors.append("Hire date cannot be in the future.")

    return errors
