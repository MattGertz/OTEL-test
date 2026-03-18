"""Exceptions for the Nearest City Service SDK."""

from .models import ErrorResponse


class NearestCityServiceError(Exception):
    """Raised when the Nearest City Service returns an error response."""

    def __init__(self, error: ErrorResponse) -> None:
        self.code = error.code
        self.message = error.message
        super().__init__(f"[{error.code}] {error.message}")
