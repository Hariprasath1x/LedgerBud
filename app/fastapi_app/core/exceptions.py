"""Domain exceptions used by the authentication service."""


class LedgerBudError(Exception):
    """Base error for business-level failures."""


class UserAlreadyExistsError(LedgerBudError):
    """Raised when a user tries to register with a duplicate email."""


class AuthenticationError(LedgerBudError):
    """Raised when credentials or tokens are invalid."""


class InactiveUserError(LedgerBudError):
    """Raised when a disabled account attempts to access protected routes."""
