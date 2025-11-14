"""
Global constants for the application.
"""

# Admin users allowed to manage categories and other sensitive operations
# These usernames correspond to Telegram usernames
ADMIN_USERS = [
    "HK_688",
    "houhokheng",
    "autosum_kh",
    "chanhengsng"
]


def is_admin_user(username: str | None) -> bool:
    """
    Check if a username is in the admin users list.

    Args:
        username: Telegram username to check

    Returns:
        True if user is admin, False otherwise

    Examples:
        >>> is_admin_user("HK_688")
        True
        >>> is_admin_user("random_user")
        False
        >>> is_admin_user(None)
        False
    """
    if not username:
        return False
    return username in ADMIN_USERS
