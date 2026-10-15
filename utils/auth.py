
"""Authentication and role-based access control helpers."""

import hashlib
import hmac
import secrets

import streamlit as st

from db.db_manager import DatabaseConnection


ROLES = {
    "Admin",
    "HR",
    "Department Manager",
    "Project Manager",
    "Executive",
}

# Keep permissions centralized so pages use consistent authorization rules.


ROLE_PERMISSIONS = {
    "Admin": {
        "manage_users",
        "view_employees",
        "manage_employees",
        "view_reviews",
        "create_reviews",
        "manage_reviews",
        "view_projects",
        "manage_projects",
        "view_department_analytics",
        "view_organization_analytics",
    },
    "HR": {
        "view_employees",
        "manage_employees",
        "view_reviews",
        "create_reviews",
        "manage_reviews",
        "view_department_analytics",
    },
    "Department Manager": {
        "view_employees",
        "view_reviews",
        "create_reviews",
        "manage_reviews",
        "view_projects",
        "view_department_analytics",
    },
    "Project Manager": {
        "view_employees",
        "view_projects",
        "manage_projects",
    },
    "Executive": {
        "view_reviews",
        "create_reviews",
        "manage_reviews",
        "view_projects",
        "view_department_analytics",
        "view_organization_analytics",
    },
}


PBKDF2_ITERATIONS = 600_000


def hash_password(password, salt=None):
    """Return a salted PBKDF2-SHA256 password hash."""
    if not isinstance(password, str) or len(password) < 12:
        raise ValueError("Password must contain at least 12 characters.")

    salt = salt or secrets.token_bytes(16)

    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )

    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${derived_key.hex()}"


def verify_password(password, stored_hash):
    """Verify a password against its stored salted hash."""
    try:
        algorithm, iterations, salt_hex, expected_hex = stored_hash.split("$")

        if algorithm != "pbkdf2_sha256":
            return False

        iterations = int(iterations)

        if not 100_000 <= iterations <= 2_000_000:
            return False

        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(expected_hex)

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations,
        )

        return hmac.compare_digest(actual, expected)

    except (AttributeError, TypeError, ValueError):
        return False


def create_auth_tables():
    """Create the application users table if it does not exist."""
    db = DatabaseConnection()

    query = """
        CREATE TABLE IF NOT EXISTS app_users (
            user_id BIGINT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL,
            department_id INT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT chk_app_user_role CHECK (
                role IN (
                    'Admin',
                    'HR',
                    'Department Manager',
                    'Project Manager',
                    'Executive'
                )
            )
        )
    """

    if not db.execute(query):
        raise RuntimeError("Could not create the authentication table.")


def authenticate(username, password):
    """Return a user record for valid active credentials, otherwise None."""
    username = username.strip()

    if not username or not password:
        return None

    db = DatabaseConnection()

    try:
        users = db.fetch_checked(
            """
            SELECT
                user_id,
                username,
                password_hash,
                role,
                department_id
            FROM app_users
            WHERE username = %s AND is_active = TRUE
            LIMIT 1
            """,
            (username,),
        )
    except RuntimeError:
        raise RuntimeError("Unable to verify login credentials.") from None

    if not users:
        return None

    user = users[0]

    if not verify_password(password, user["password_hash"]):
        return None

    if user["role"] not in ROLES:
        return None

    return {
        "user_id": user["user_id"],
        "username": user["username"],
        "role": user["role"],
        "department_id": user["department_id"],
    }


def has_permission(permission):
    """Check whether the logged-in user has a named permission."""
    user = st.session_state.get("auth_user")

    if not user:
        return False

    return permission in ROLE_PERMISSIONS.get(user.get("role"), set())


def require_login():
    """Stop page execution when no user is logged in."""
    if not st.session_state.get("auth_user"):
        st.warning("Please log in to access this page.")
        st.stop()


def require_permission(permission):
    """Stop page execution when the logged-in user lacks permission."""
    require_login()

    if not has_permission(permission):
        st.error("You do not have permission to perform this action.")
        st.stop()


def logout():
    """Clear authentication state for the current Streamlit session."""
    st.session_state.pop("auth_user", None)
    st.rerun()
