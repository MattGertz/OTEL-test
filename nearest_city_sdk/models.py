"""Models for the Nearest City Service SDK."""

from dataclasses import dataclass


@dataclass
class City:
    """A city result returned by the Nearest City Service."""

    name: str
    """City name."""

    country: str
    """Country the city belongs to."""

    population: int
    """City population."""

    distance_km: float
    """Distance from the queried coordinate in kilometers."""

    latitude: float
    """City center latitude."""

    longitude: float
    """City center longitude."""


@dataclass
class ErrorResponse:
    """Error response from the Nearest City Service."""

    code: int
    """Error code."""

    message: str
    """Error message."""
