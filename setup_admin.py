
"""Create the first application administrator interactively."""

import getpass
import re

from db.db_manager import DatabaseConnection
from utils.auth import create_auth_tables, hash_password


def main():
    """Create an Admin account if one does not already exist."""
    try:
        create_auth_tables()
    except Exception as exc:
        print(f"Could not initialize the authentication table: {exc}")
        return

    db = DatabaseConnection()

    try:
        admins = db.fetch_checked(
            "SELECT COUNT(*) AS total FROM app_users WHERE role = %s",
            ("Admin",),
        )
    except RuntimeError:
        print("Could not check the existing administrator accounts.")
        return

    if admins[0]["total"] > 0:
        print("An Admin account already exists. Setup is disabled.")
        return

    print("\nInitial Administrator Setup")
    print("----------------------------")

    username = input("Choose an admin username: ").strip()

    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,100}", username):
        print(
            "Username must be 3–100 characters and contain only "
            "letters, numbers, periods, underscores, or hyphens."
        )
        return

    password = getpass.getpass("Choose a password (minimum 12 characters): ")
    confirmation = getpass.getpass("Confirm password: ")

    if password != confirmation:
        print("Passwords do not match.")
        return

    try:
        password_hash = hash_password(password)
    except ValueError as exc:
        print(exc)
        return

    # Recheck before inserting to reduce the chance of concurrent setup.
    try:
        admins = db.fetch_checked(
            "SELECT COUNT(*) AS total FROM app_users WHERE role = %s",
            ("Admin",),
        )
    except RuntimeError:
        print("Could not verify administrator status. No account was created.")
        return

    if admins[0]["total"] > 0:
        print("An Admin account was created by another setup process.")
        return

    # The database's unique username constraint prevents duplicate usernames.
    if not db.execute(
        """
        INSERT INTO app_users (username, password_hash, role, is_active)
        VALUES (%s, %s, %s, TRUE)
        """,
        (username, password_hash, "Admin"),
    ):
        print("Could not create the administrator. Check database connectivity.")
        return

    print(f"\nAdministrator '{username}' created successfully.")
    print("Keep your password private.")


if __name__ == "__main__":
    main()
